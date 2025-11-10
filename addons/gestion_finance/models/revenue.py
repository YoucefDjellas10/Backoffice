from odoo import fields, models, api
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime


class Revenue(models.Model):
    _name = 'revenue.record'
    _description = 'Recette'

    name = fields.Char(string='Id', readonly=True, copy=False)
    verifier = fields.Selection([('non_verifier', 'Non Versé'),
                                 ('demender', 'Demandé'),
                                ('verifier', 'Versé')], string='Etat de versement', default='non_verifier')
    reservation = fields.Many2one('reservation', string='Reservation')
    livraison = fields.Many2one('livraison', string='Livraison')
    vehicule = fields.Many2one(string='Véhicule', related='reservation.vehicule', store=True)
    modele = fields.Many2one(string='Modele', related='reservation.modele', store=True)
    zone = fields.Many2one(string='Zone', related='reservation.zone', store=True)
    currency_id = fields.Many2one(string='Currency', related='reservation.currency_id_reduit', store=True)
    total_reduit_euro = fields.Monetary(string='total (Euro)', currency_field='currency_id',
                                        related='reservation.total_reduit_euro', store=True)
    euro = fields.Many2one('res.currency', string='euro', default=lambda self: self.env['res.currency'].browse(125).id)
    montant = fields.Monetary(string='Montant €', currency_field='euro')
    montant_eur_dzd = fields.Monetary(string='Montant € TO DA', currency_field='dinar',
                                      compute='_compute_montant_eur_dzd', store=True)
    dinar = fields.Many2one('res.currency', string='Dinar algérien',
                            default=lambda self: self.env['res.currency'].browse(111).id)
    montant_dzd = fields.Monetary(string='Montant DA', currency_field='dinar')
    montant_dzd_eur = fields.Monetary(string='Montant DA TO €', currency_field='euro',
                                      compute='_compute_montant_eur_dzd', store=True)
    note = fields.Text(string='Note')
    total_reduit_dinar = fields.Monetary(string='A encaisser (Dinar)', currency_field='dinar',
                                         compute='_compute_total_reduit_dinar', store=True)
    ecart_eur = fields.Monetary(string='Ecart €', currency_field='euro', related='reservation.reste_payer', store=True)
    ecart_da = fields.Monetary(string='Ecart DA', currency_field='dinar', compute='_compute_ecart_eur_dinar',
                               store=True)
    mode_paiement = fields.Selection([('carte', 'Banque'),
                                      ('liquide', 'Liquide'),
                                      ('autre', 'Autre')], string='Mode de paiement', required=True)
    total_encaisse = fields.Monetary(string='Total', currency_field='dinar', compute='_compute_ecart_eur_dinar',
                                     store=True)

    @api.depends('total_reduit_euro', 'total_reduit_dinar', 'montant', 'montant_eur_dzd', 'montant_dzd',
                 'montant_dzd_eur', 'total_encaisse')
    def _compute_ecart_eur_dinar(self):
        for record in self:
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            if taux_change:
                taux = taux_change.montant
                record.ecart_da = record.ecart_eur * taux

    @api.depends('montant', 'montant_dzd')
    def _compute_montant_eur_dzd(self):
        for record in self:
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            if taux_change:
                taux = taux_change.montant
                record.montant_eur_dzd = record.montant * taux
                record.montant_dzd_eur = record.montant_dzd / taux
            else:
                record.montant_eur_dzd = 0
                record.montant_dzd_eur = 0

    @api.depends('total_reduit_euro')
    def _compute_total_reduit_dinar(self):
        for record in self:
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            if taux_change:
                taux = taux_change.montant
                record.total_reduit_dinar = record.total_reduit_euro * taux
            else:
                record.total_reduit_dinar = 0

    
    @api.model
    def create(self, vals):
        montant = vals.get('montant', 0) or 0
        montant_dzd = vals.get('montant_dzd', 0) or 0
        if montant <= 0 and montant_dzd <= 0:
            raise UserError("Impossible de créer une recette : le montant en € ou en Dinar doit être supérieur à 0.")
        record = super(Revenue, self).create(vals)
        record.name = 'R-{:03d}'.format(record.id)
        return record


    @api.model
    def action_search_revenues(self, filters=False, page=1, limit=30):
        """
        Recherche les encaissements selon les filtres donnés par le frontend OWL.
        """
        domain = []

        if filters:
            # Filtre réservation par texte (recherche sur le champ name)
            if filters.get('reservation'):
                reservation_ref = filters['reservation'].strip()
                # Recherche les réservations dont le name contient la référence
                reservation_ids = self.env['reservation'].search([
                    ('name', 'ilike', reservation_ref)
                ]).ids
                if reservation_ids:
                    domain.append(('reservation', 'in', reservation_ids))
                else:
                    # Aucune réservation trouvée, on retourne un résultat vide
                    domain.append(('reservation', '=', False))

            if filters.get('zone'):
                domain.append(('zone', '=', filters['zone']))
            if filters.get('vehicule'):
                domain.append(('vehicule', '=', filters['vehicule']))
            if filters.get('mode_paiement'):
                domain.append(('mode_paiement', '=', filters['mode_paiement']))
            if filters.get('effectue_par'):
                domain.append(('create_uid', '=', filters['effectue_par']))

            # Filtres date : Du / Au - Recherche sur create_date OU reservation.create_date
            du_str = filters.get('du')
            au_str = filters.get('au')
            if du_str and au_str:
                try:
                    du = datetime.strptime(du_str, '%Y-%m-%d')
                    au = datetime.strptime(au_str, '%Y-%m-%d')
                    au = au.replace(hour=23, minute=59, second=59)

                    # Domaine pour les dates : (create_date entre du et au) OU (create_date vide ET reservation.create_date entre du et au)
                    date_domain = [
                        '|',
                        '&', ('create_date', '>=', du), ('create_date', '<=', au),
                        '&', ('create_date', '=', False),
                        '&', ('reservation.create_date', '>=', du), ('reservation.create_date', '<=', au)
                    ]

                    # Ajouter le domaine de dates au domaine principal
                    domain.extend(date_domain)

                except Exception as e:
                    print(f"Erreur conversion date: {e}")

        # Pagination
        offset = (page - 1) * limit

        # Recherche
        revenues = self.search(domain, offset=offset, limit=limit, order='id desc')
        total_count = self.search_count(domain)

        # Calcul des totaux (toutes lignes correspondantes)
        total_records = self.search(domain)


        total_montant_dzd = sum(total_records.mapped('montant_dzd'))
        total_montant_eur = sum(total_records.mapped('montant'))

        # Formatage pour le frontend
        revenues_data = []
        for rev in revenues:
            # Déterminer la date à afficher : create_date du revenue ou create_date de la réservation
            display_date = rev.create_date
            if not display_date and rev.reservation and rev.reservation.create_date:
                display_date = rev.reservation.create_date

            revenues_data.append({
                'id': rev.id,
                'reservation_ref': rev.reservation.name if rev.reservation else '',
                'create_date': display_date.strftime('%d/%m/%Y %H:%M') if display_date else '',
                'effectuer_par': rev.create_uid.name if rev.create_uid else '',
                'mode_paiement': dict(rev._fields['mode_paiement'].selection).get(rev.mode_paiement, ''),
                'montant_eur': f"{rev.montant:.2f}",
                'montant_dzd': f"{rev.montant_dzd:.2f}",
            })


        return {
            'revenues': revenues_data,
            'total_count': total_count,
            'total_montant_dzd': round(total_montant_dzd, 2),
            'total_montant_eur': round(total_montant_eur, 2),
        }


class ReservationInheritRevenue(models.Model):
    _inherit = 'reservation'

    revenue_ids = fields.One2many('revenue.record', 'reservation', string='Revenues')
    total_revenue = fields.Float(string="Total Encaisser", compute="_compute_total_revenue", store=True)

    @api.depends('revenue_ids.montant')
    def _compute_total_revenue(self):
        for record in self:
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)

            record.total_revenue = sum(record.revenue_ids.mapped('montant')) + sum(
                record.revenue_ids.mapped('montant_dzd')) / taux_change.montant

    def action_calculate_total_revenue(self):
        """
        Méthode pour calculer le total_revenue pour toutes les réservations
        contenant 'SEA' dans le nom
        """
        try:
            # Récupérer le taux de change une seule fois
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)

            if not taux_change:
                raise ValueError("Le taux de change n'a pas été trouvé")

            if taux_change.montant == 0:
                raise ZeroDivisionError("Le taux de change ne peut pas être zéro")

            # Récupérer toutes les réservations contenant 'SEA'
            reservations = self.env['reservation'].search([
                ('name', 'ilike', 'SEA')
            ])

            if not reservations:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Information',
                        'message': "Aucune réservation trouvée contenant 'SEA'",
                        'type': 'info',
                        'sticky': False,
                    }
                }

            # Parcourir toutes les réservations et calculer le total_revenue
            count_success = 0
            for record in reservations:
                try:
                    montant_principal = sum(record.revenue_ids.mapped('montant'))
                    montant_dzd_converti = sum(record.revenue_ids.mapped('montant_dzd')) / taux_change.montant
                    record.total_revenue = montant_principal + montant_dzd_converti
                    count_success += 1
                except Exception as e:
                    _logger.error(f"Erreur lors du calcul pour {record.name}: {str(e)}")

            # Notification de succès
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Succès',
                    'message': f"{count_success} réservation(s) calculée(s) avec succès",
                    'type': 'success',
                    'sticky': False,
                }
            }

        except ZeroDivisionError:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': "Le taux de change ne peut pas être zéro",
                    'type': 'danger',
                    'sticky': True,
                }
            }
        except ValueError as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': f"Une erreur s'est produite: {str(e)}",
                    'type': 'danger',
                    'sticky': True,
                }
            }


class LivraisonInheritRevebue(models.Model):
    _inherit = 'livraison'

    revenue_ids = fields.One2many('revenue.record', 'livraison', string='Revenues')
    reservation = fields.Many2one('reservation', string='Reservation')
    total_payer = fields.Float(string="Total à payer €", compute='compute_total_payer', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.ref('base.EUR').id)
    currency_da = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.ref('base.DZD').id)
    montant_euro_pay = fields.Monetary(currency_field='currency_id', string='Montant €')
    montant_euro_ecart = fields.Monetary(currency_field='currency_id', string='Ecart €',
                                         compute='calculate_change_da', store=True)
    montant_dz_pay = fields.Monetary(currency_field='currency_da', string='Montant DA')
    montant_dz_ecart = fields.Monetary(currency_field='currency_da', string='Ecart DA',
                                       compute='calculate_change_da', store=True)
    total_payer_dz = fields.Monetary(currency_field='currency_da', string='Total à payer DA',
                                     compute='calculate_change_da', store=True)

    @api.onchange('montant_euro_pay', 'montant_dz_pay', 'total_payer_dz', 'total_payer')
    def calculate_change_da(self):
        for record in self:

            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            if taux_change:
                taux = taux_change.montant
                record.montant_dz_ecart = record.total_payer * taux - record.montant_euro_pay * taux - record.montant_dz_pay
                record.total_payer_dz = record.total_payer * taux
                record.montant_euro_ecart = record.total_payer - record.montant_euro_pay - record.montant_dz_pay / taux

    def action_create_revenue(self):
        for record in self:
            if not record.reservation:
                raise UserError("Aucune réservation associée à cette livraison.")

            if record.nd_driver_ajoute:
                if not record.nd_client_lv and not record.nd_client_nom:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Information client manque',
                            'message': 'Veillez remplir les informations client pour continuer.',
                            'type': 'danger'
                        }
                    }


                if record.nd_client_lv and record.nd_client_lv.risque == 'eleve':
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Client Bloqué',
                            'message': 'Le client est bloqué vous ne pouvez pas l\'ajouter à cette reservation.',
                            'type': 'danger'
                        }
                    }
                elif record.nd_client_lv and record.nd_client_lv.risque != 'eleve':
                    record.reservation.nd_client = record.nd_client_lv
                elif record.nd_client_nom :
                    nom = " ".join(record.nd_client_nom.upper().split())
                    prenom = " ".join(record.nd_client_prenom.upper().split()) if record.nd_client_prenom else ""
                    client_existant = self.env['liste.client'].search([
                        ('nom', '=', nom),
                        ('prenom', '=', prenom)
                    ], limit=1)
                    if not client_existant:
                        client_existant = self.env['liste.client'].search([
                            ('nom', '=', prenom),
                            ('prenom', '=', nom)
                        ], limit=1)
                    if client_existant and client_existant.risque == 'eleve' :
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': 'Client Bloqué',
                                'message': 'Le client est bloqué vous ne pouvez pas l\'ajouter à cette reservation.',
                                'type': 'danger'
                            }
                        }
                    elif client_existant and client_existant.risque != 'eleve' :
                        record.reservation.nd_client = client_existant
                    elif not client_existant :
                        client_existant = self.env['liste.client'].search([
                            ('nom', '=', nom),
                            ('prenom', '=', prenom),
                            ('date_de_naissance', '=', record.nd_client_birthday),
                            ('date_de_permis', '=', record.nd_client_permis_date)
                        ], limit=1)
                        record.reservation.nd_client = client_existant

                option_nd_driver = self.env['options'].search([('option_code', '=', 'ND_DRIVER')], limit=1)
                record.reservation.opt_nd_driver = option_nd_driver

                record.nd_driver_total = 0

            if record.sb_ajout:
                option_siege_bebe = self.env['options'].search([('option_code', '=', 'S_BEBE_5')], limit=1)
                record.reservation.opt_siege_a = option_siege_bebe
                record.sb_total = 0
            if record.max_ajoute:
                option_max = self.env['options'].search([
                    ('option_code', 'ilike', 'MAX'),
                    ('categorie', '=', record.vehicule.categorie.id)
                ], limit=1)
                record.reservation.opt_protection = option_max
                record.max_total = 0
            if record.standart_ajoute:
                option_standart = self.env['options'].search([
                    ('option_code', 'ilike', 'STANDART'),
                    ('categorie', '=', record.vehicule.categorie.id)
                ], limit=1)
                record.reservation.opt_protection = option_standart
                record.standart_total = 0

            if record.carburant_ajoute:
                option_carburant = self.env['options'].search([('option_code', '=', 'P_CARBURANT')], limit=1)
                record.reservation.opt_plein_carburant = option_carburant
                record.carburant_total_f= 0

            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)

            self.env['revenue.record'].create({
                'reservation': record.reservation.id,
                'livraison': record.id,
                'montant': record.montant_euro_pay,
                'montant_dzd': record.montant_dz_pay,
                'ecart_eur': record.montant_euro_ecart,
                'ecart_da': record.montant_dz_ecart,
                'mode_paiement': 'liquide',
                'total_encaisse': record.montant_dz_pay + record.montant_euro_pay * taux_change.montant
            })

            record.montant_euro_pay = 0

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'success',
                    'message': 'Record Enregistrer avec succé.',
                    'type': 'success'
                }
            }

    def action_create_degradation(self):
        for record in self:
            if not record.reservation:
                raise UserError("Aucune réservation associée à cette livraison.")
            record.reservation.total_degrader = record.total_eur
            record.reservation.total_ecce_klm = record.penalit_klm

            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            if record.montant_dz_pay > 0 or record.montant_euro_pay > 0 :
                self.env['revenue.record'].create({
                    'reservation': record.reservation.id,
                    'livraison': record.id,
                    'montant': record.montant_euro_pay,
                    'montant_dzd': record.montant_dz_pay,
                    'ecart_eur': record.montant_euro_ecart,
                    'ecart_da': record.montant_dz_ecart,
                    'mode_paiement': 'liquide',
                    'total_encaisse': record.montant_dz_pay + record.montant_euro_pay * taux_change.montant
                })
                record.montant_euro_pay = 0
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'success',
                        'message': 'Record Enregistrer avec succé.',
                        'type': 'success'
                    }
                }
            else :
                record.montant_euro_pay = 0
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Montant invalid',
                        'message': 'Veliiez remplir le montant à payé.',
                        'type': 'warning'
                    }
                }







