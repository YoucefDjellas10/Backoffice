from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import base64
from datetime import datetime, timedelta, date

from io import BytesIO
from PyPDF2 import PdfMerger


class Livraison(models.Model):
    _name = 'livraison'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'livraison des vehicules'

    name = fields.Char(string='Nom')
    reservation = fields.Many2one('reservation', string='Reservation')
    total_prolone = fields.Integer(string='Prolongation', related='reservation.total_prolone', store=True)
    total_prolone_eur = fields.Monetary(string='Prolongation', currency_field='currency_id',
                                        compute='_compute_total_amount', store=True)
    lv_type = fields.Selection([('livraison', 'D'), ('restitution', 'R')], string='Lv type')
    status = fields.Selection(string='Etat', related='reservation.status', store=True)
    note_lv_d = fields.Text(string='Note', related='reservation.note_lv_d', store=True)
    note_lv_r = fields.Text(string='Note', related='reservation.note_lv_r', store=True)
    date_heure_debut = fields.Datetime(string='Date', related='reservation.date_heure_debut', store=True)
    date_heure_debut_format = fields.Char(string='Date heure debut',
                                          compute='_compute_date_heure_debut_format')

    def _compute_date_heure_debut_format(self):
        for record in self:
            if record.date_heure_debut:
                record.date_heure_debut_format = record.date_heure_debut.strftime('%d-%m-%Y %H:%M')
            else:
                record.date_heure_debut_format = ''

    date_de_reservation = fields.Datetime(string='Date de reservation', related='reservation.create_date', store=True)
    date_heure_fin = fields.Datetime(string='Date', related='reservation.date_heure_fin', store=True, readonly=False)
    nbr_jour_reservation = fields.Integer(string='Durée', related='reservation.nbr_jour_reservation', store=True)
    duree_dereservation = fields.Char(string='Durée', related='reservation.duree_dereservation', store=True)

    lieu_depart = fields.Many2one(string='Lieu', related='reservation.lieu_depart', store=True)
    zone = fields.Many2one(string='Zone', related='reservation.zone', store=True)
    lieu_retour = fields.Many2one(string='Lieu', related='reservation.lieu_retour', store=True, readonly=False)
    vehicule = fields.Many2one(string='Véhicule', related='reservation.vehicule', store=True)
    modele = fields.Many2one(string='Modele', related='reservation.modele', store=True)

    categorie = fields.Many2one(string='categorie', related='reservation.categorie', store=True)
    caution_classic = fields.Float(string='Caution classique', related='categorie.caution_classic', store=True)
    caution_red = fields.Float(string='Caution Réduite', related='categorie.caution_red', store=True)
    caution_classic_eur = fields.Monetary(string='Caution', currency_field='currency_id',
                                          compute='_compute_total_amount', store=True)

    opt_protection_caution = fields.Integer(string='Caution', related='reservation.opt_protection_caution', store=True)

    carburant = fields.Selection(string='Carburant', related='reservation.carburant', store=True)
    date_debut_service = fields.Date(string='Date mis en service', related='reservation.date_debut_service', store=True)
    date_fin_service = fields.Date(string='Date fin de service', related='reservation.date_fin_service', store=True)
    matricule = fields.Char(string='Matricule', related='reservation.matricule', store=True)
    numero = fields.Char(string='Numéro', related='reservation.numero', store=True)
    nd_conducteur = fields.Selection([('oui', 'oui'), ('non', 'non')], string='2eme condicteur',
                                     related='reservation.nd_conducteur', readonly=False)
    civilite_nd_condicteur = fields.Selection([('Mr', 'M.'), ('Mme', 'Mme'), ('Mlle', 'Mlle')], string='Civilité',
                                              related='reservation.civilite_nd_condicteur')
    nom_nd_condicteur = fields.Char(string='Nom', related='reservation.nom_nd_condicteur')
    prenom_nd_condicteur = fields.Char(string='Prénom', related='reservation.prenom_nd_condicteur')
    email_nd_condicteur = fields.Char(string='Email', related='reservation.email_nd_condicteur')
    date_nd_condicteur = fields.Date(string='Date de naissance', related='reservation.date_nd_condicteur')
    date_de_permis = fields.Date(string='Date de permis', related='reservation.date_de_permis')

    client = fields.Many2one(related='reservation.client', store=True)
    nom = fields.Char(string='Nom', related='reservation.nom', store=True)
    prenom = fields.Char(string='Prénom', related='reservation.prenom', store=True)
    email = fields.Char(string='Email', related='reservation.email', store=True)
    date_de_naissance = fields.Date(string='Date de naissance', related='reservation.date_de_naissance', store=True)
    mobile = fields.Char(string='Mobile', related='reservation.mobile', store=True)
    telephone = fields.Char(string='Téléphone', related='reservation.telephone', store=True)
    risque = fields.Selection(string='Risque', related='reservation.risque', store=True)
    note = fields.Text(string='Note', related='reservation.note', store=True)

    prix_jour = fields.Integer(string='Prix par jours', related='reservation.prix_jour', store=True)
    prix_jour_two = fields.Integer(string='Prix Jour Two', related='reservation.prix_jour_two', store=True)
    nbr_jour_two = fields.Integer(string='Nombre de Jours Two', related='reservation.nbr_jour_two', store=True)
    nbr_jour_one = fields.Integer(string='Nombre de Jours One', related='reservation.nbr_jour_one', store=True)
    frais_de_livraison = fields.Integer(string='Frais de livraison', related='reservation.frais_de_livraison',
                                        store=True)
    options_total = fields.Integer(string='Total des options', related='reservation.options_total', store=True)
    total = fields.Integer(string='Total Général', related='reservation.total', store=True)
    total_afficher = fields.Integer(string='Total Afficher', related='reservation.total_afficher', store=True)
    prix_jour_afficher = fields.Float(string='Prix par jour Afficher', related='reservation.prix_jour_afficher',
                                      store=True)
    supplements = fields.Integer(string='Supplements', related='reservation.supplements', store=True)
    retour_tard = fields.Integer(string='Retour tard', related='reservation.retour_tard', store=True)
    retour_avance = fields.Boolean(string='Retour a l\' avance', related='reservation.retour_avance', store=True)
    date_retour_avance = fields.Datetime(string='Retour a l\'avance', related='reservation.date_retour_avance',
                                         store=True)

    kilomtrage = fields.Integer(string='Kilometrage')
    kilometrage_depart = fields.Integer(string='Kilometrage depart', related='reservation.kilometrage_depart',
                                        store=True)
    penalit_klm = fields.Monetary(currency_field='currency_id', compute='action_calculate_klm',
                                  string='Penalité KM', store=True)
    penalit_klm_dinar = fields.Monetary(currency_field='currency_da', string='Penalité KM (DA)',
                                        compute='action_calculate_klm_da', store=True)
    diff_klm = fields.Integer(string='Differance KM')

    @api.depends('penalit_klm', 'kilomtrage')
    def action_calculate_klm_da(self):
        for record in self:
            taux_change = self.env['taux.change'].browse([2])
            record.penalit_klm_dinar = record.penalit_klm * taux_change.montant

    @api.depends('kilomtrage')
    def action_calculate_klm(self):
        for record in self:
            if record.lv_type is not None and record.lv_type != 'livraison' and not record.reservation.opt_klm:
                diff = 0
                dif = diff
                penalite_klm = 0
                diff = record.kilomtrage - record.kilometrage_depart
                option_klm = self.env['options'].search([
                    ('option_code', 'ilike', 'KLM_ILLIMITED'),
                    ('categorie', '=', record.vehicule.categorie.id)
                ], limit=1)
                limit_klm = option_klm.limit_Klm * record.nbr_jour_reservation
                if diff > limit_klm:
                    penalite_klm = option_klm.penalite_Klm * (diff - limit_klm)
                    baremes = self.env['bareme.degradation'].browse([135, 136, 137])
                    type_deg = self.env['type.degradation'].browse(20)

                    for bareme in baremes:
                        if record.vehicule.modele.categorie.id == bareme.categorie.id and record.lv_type == 'restitution':
                            dif = diff

                record.penalit_klm = penalite_klm
                record.diff_klm = (diff - limit_klm)

    etat_carburant_retour = fields.Selection([('plein', 'Plein carburant'),
                                              ('demi', '1/2 Un demi'),
                                              ('quart', '1/4 Un quart'),
                                              ('tiere', '3/4 Trois quarts')], string='Etat du carburant')
    penalit_carburant = fields.Monetary(currency_field='currency_da', string='Penalité Carburant',
                                        compute='action_calculate_carburant', store=True)
    penalit_carburant_euro = fields.Monetary(currency_field='currency_id', string='Penalité Carburant',
                                             compute='action_calculate_carburant_euro', store=True)

    @api.depends('penalit_carburant', 'etat_carburant_retour')
    def action_calculate_carburant_euro(self):
        for record in self:
            taux_change = self.env['taux.change'].browse([2])
            record.penalit_carburant_euro = record.penalit_carburant / taux_change.montant

    @api.depends('etat_carburant_retour')
    def action_calculate_carburant(self):
        for record in self:
            if not record.reservation.opt_plein_carburant_name:
                carburant_bareme = self.env['type.degradation'].search([
                    ('name', 'ilike', 'carburant'),
                ], limit=1)

                if record.etat_carburant_retour == "demi":
                    bareme = self.env['bareme.degradation'].search([
                        ('type', '=', carburant_bareme.id),
                        ('name', 'ilike', 'Réservoir rempli à moitié'),
                    ], limit=1)
                    record.penalit_carburant = bareme.prix if bareme else 0

                elif record.etat_carburant_retour == "tiere":
                    bareme = self.env['bareme.degradation'].search([
                        ('type', '=', carburant_bareme.id),
                        ('name', 'ilike', 'Réservoir rempli au 3/4'),
                    ], limit=1)
                    record.penalit_carburant = bareme.prix if bareme else 0

                elif record.etat_carburant_retour == "quart":
                    bareme = self.env['bareme.degradation'].search([
                        ('type', '=', carburant_bareme.id),
                        ('name', 'ilike', 'Réservoir au 1/4'),
                    ], limit=1)
                    record.penalit_carburant = bareme.prix if bareme else 0

                else:
                    record.penalit_carburant = 0

    siege_bebe = fields.Boolean(string='Siège bébé')
    document_vehicule = fields.Boolean(string='Document véhicule', default=True)
    garantie = fields.Boolean(string='Caution déposé', default=False)
    roue_de_secours = fields.Boolean(string='Roue de secours & cric', default=True)
    etat_carburant = fields.Selection([('plein', 'Plein carburant'),
                                       ('demi', '1/2 Un demi'),
                                       ('tiere', '3/4 Trois quarts'),
                                       ('quart', '1/4 Un quart')], string='Etat du carburant')

    document_fournis = fields.Selection([('passport', 'Passport'), ('cin', 'CIN')], string='document founis')
    signature = fields.Binary(string='Signature', store=True)
    photo = fields.Many2many('ir.attachment', string='Photos')
    photo_degat = fields.Many2many('ir.attachment', 'livraison_photo_degat_rel', string='Photos des dégâts')
    nd_condicteur = fields.Boolean(string='2ème condicteur')
    plein_carburant = fields.Boolean(string='Plein carburant')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.ref('base.EUR').id)
    currency_da = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.ref('base.DZD').id)
    total_amount = fields.Monetary(string='Total', currency_field='currency_id', store=True,
                                   compute='_compute_total_amount')
    dernier_klm = fields.Integer(string='dernier kilometraeg', related='vehicule.dernier_klm')
    stage = fields.Selection([('reserve', 'Planifié'), ('livre', 'Livré')], string='Stage', default='reserve')
    livrer_par = fields.Many2one('res.users', string='Livré par')
    livrer_par_one = fields.Many2one(string='Livré par', related='reservation.livrer_par')
    photo_depart = fields.Many2many(string='Photos depart', related='reservation.photo_depart')
    degradation = fields.One2many('degradation', 'livraison', string='Dégradation')

    total_da = fields.Monetary(string='Total dégradation', currency_field='currency_da', compute='_compute_total_da',
                               store=True)
    total_eur = fields.Monetary(string='Dégradation', currency_field='currency_id', compute='_compute_total_eur',
                                store=True)
    total_restitution_eur = fields.Monetary(string='Total', currency_field='currency_id',
                                            compute='_compute_total_restitution_eur', store=True)
    lv_note = fields.Text(string='Note')
    assurance_complementaire = fields.Boolean(string='Assurance Complementaire')
    change_lieu_retour = fields.Boolean(string='Change lieu de retour', default=False)
    change_heure_retour = fields.Boolean(string='Change heure de retour', default=False)
    action_date = fields.Datetime(string='Date', compute='_compute_action_date', store=True)
    action_lieu = fields.Char(string='Lieu', compute='_compute_action_date', store=True)
    color = fields.Integer(string='color', compute='_compute_action_date', store=True)
    total_reduit_euro = fields.Monetary(string='Total à payer', currency_field='currency_id',
                                        related='reservation.reste_payer', store=True)

    date_retour_one = fields.Datetime(string='Ancienne Date retoure', related='reservation.date_heure_fin', store=True)
    lieu_retour_one = fields.Many2one('lieux', string='Ancien Lieu retour', related='reservation.lieu_retour',
                                      store=True)
    total_rduit_one = fields.Monetary(string='Ancien Total', currency_field='currency_id')

    opt_carburant = fields.Many2one(string='Carburant option', related='reservation.opt_plein_carburant', store=True)
    opt_carburant_check = fields.Boolean(string='Plein Carburant')
    opt_klm = fields.Many2one(string='Kilometrage illimité option', related='reservation.opt_klm', store=True)
    opt_klm_check = fields.Boolean(string='Kilometrage illimité')
    opt_nd_driver = fields.Many2one(string='2èeme conducteur option', related='reservation.opt_nd_driver', store=True)
    opt_nd_driver_check = fields.Boolean(string='2èeme conducteur')
    opt_sb_a = fields.Many2one(string='Baby seat (3-9 kg)  option', related='reservation.opt_siege_a', store=True)
    opt_sb_a_check = fields.Boolean(string='Baby seat (3-9 kg)')
    opt_sb_b = fields.Many2one(string='Baby seat (9-13 kg) option', related='reservation.opt_siege_b', store=True)
    opt_sb_b_check = fields.Boolean(string='Baby seat (9-13 kg)')
    opt_sb_c = fields.Many2one(string='Baby seat (10-18 kg) option', related='reservation.opt_siege_c', store=True)
    opt_sb_c_check = fields.Boolean(string='Baby seat (10-18 kg)')

    opt_protection = fields.Char(string='Protection option', related='reservation.opt_protection_name', store=True,
                                 readonly=True)

    nd_client_lv = fields.Many2one('liste.client', string='Client existant')
    nd_client_nom = fields.Char(string='Nom')
    nd_client_prenom = fields.Char(string='Prénom')
    nd_client_birthday = fields.Date(string='Date de naissance')
    nd_client_permis_date = fields.Date(string='Date de permis')

    sous_total = fields.Float(string="Total ajouté", default=0)
    changed_hour = fields.Datetime(string='Nouvelle Heure', compute='changed_place_hour', readonly=False, store=True)
    chenged_place = fields.Datetime(string='Nouveau Lieu')
    changed_place = fields.Many2one('lieux', string='Nouveau Lieu', domain="[('zone', '=', zone)]",
                                    compute='changed_place_hour', readonly=False, store=True)
    is_available = fields.Selection([('oui', 'Oui'), ('non', 'non')], string='Disponible')
    appliquer = fields.Selection([('oui', 'Oui'), ('non', 'non')], string='Disponible')

    def _convert_to_float(self, heure_datetime):
        return heure_datetime.hour + heure_datetime.minute / 60

    def action_verifier_disponibilite(self):
        for record in self:
            if not record.vehicule or not record.date_heure_debut or not record.changed_hour:
                raise UserError("Veuillez renseigner un véhicule et des dates valides.")

            if record.changed_place == record.lieu_retour and record.date_heure_fin == record.changed_hour:
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {'title': 'Pas de changement',
                                   'message': 'Veillez changer les dates ou les lieux.',
                                   'type': 'warning'
                                   }
                        }

            date_debut = record.date_heure_debut
            if record.changed_place == record.lieu_retour:
                date_fin = record.changed_hour + timedelta(hours=1)
            else:
                date_fin = record.changed_hour + timedelta(hours=3)

            conflit = self.env['reservation'].search([
                ('vehicule', '=', record.vehicule.id),
                ('status', '=', 'confirmee'),
                ('date_heure_debut', '<', date_fin),
                ('date_heure_fin', '>', date_debut),
                ('id', '!=', record.reservation.id)
            ])

            if conflit:
                record.write({'is_available': 'non', 'sous_total': 0})
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {'title': 'Vehicule None disponible',
                                   'message': 'Le véhicule n\'est pas disponible.',
                                   'type': 'danger'
                                   }
                        }
            record.is_available = 'oui'
            jours_supplementaires = (
                                            record.changed_hour.date() - record.date_heure_debut.date()).days - record.nbr_jour_reservation
            if jours_supplementaires >= 0:
                record.sous_total = record.prix_jour * jours_supplementaires
                record.write({'is_available': 'oui', 'sous_total': record.prix_jour * jours_supplementaires})
                if record.reservation.retour_tard == 0:
                    heure_debut = record.date_heure_debut.time()
                    heure_fin = record.changed_hour.time()
                    ecart = (datetime.combine(date.min, heure_fin) - datetime.combine(date.min,
                                                                                      heure_debut)).seconds / 3600.0

                    if heure_debut > heure_fin:
                        ecart = ecart - 24

                    supplements = self.env['supplements'].search([('valeur', '>', 0)])
                    retour_tard_value = 0

                    for supplement in supplements:
                        if ecart > supplement.reatrd:
                            if record.reservation.prix_jour_two > 0:
                                retour_tard_value = record.reservation.prix_jour_two * 2 / 3
                            else:
                                retour_tard_value = record.reservation.prix_jour * 2 / 3

                        record.sous_total += retour_tard_value
                supplements_value = 0

                heure_debut_float = self._convert_to_float(record.date_heure_debut + timedelta(hours=1))
                heure_fin_float = self._convert_to_float(record.changed_hour + timedelta(hours=1))

                supplements = self.env['supplements'].search([])

                for supplement in supplements:
                    if supplement.heure_debut_float <= heure_debut_float < supplement.heure_fin_float:
                        supplements_value += supplement.montant

                for supplement in supplements:
                    if supplement.heure_debut_float <= heure_fin_float < supplement.heure_fin_float:
                        supplements_value += supplement.montant
                if record.reservation.supplements < supplements_value:
                    record.sous_total += supplements_value - record.reservation.supplements

                frai_livraison_value = 0

                frais_livraison = self.env['frais.livraison'].search([
                    ('depart', '=', record.lieu_depart.id),
                    ('retour', '=', record.changed_place.id)
                ], limit=1)
                if frais_livraison:
                    frai_livraison_value += frais_livraison.montant
                else:
                    frai_livraison_value = 0

                if frai_livraison_value > record.reservation.frais_de_livraison:
                    record.sous_total += frai_livraison_value - record.reservation.frais_de_livraison

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {'title': 'Véhicule Disponible',
                               'message': f'Un supplément de {record.sous_total:.2f} sera ajouté.',
                               'type': 'success'}
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {'title': 'Véhicule Disponible',
                               'message': f'Un supplément de 00 sera ajouté.',
                               'type': 'success'}
                }

    def action_print_all_reports(self):
        if not self:
            raise UserError("Aucun enregistrement sélectionné!")
        if len(self) > 1:
            raise UserError("Cette action ne peut être effectuée que sur un seul enregistrement à la fois!")

        try:
            # Récupération des rapports avec la nouvelle syntaxe
            report1 = self.env['ir.actions.report']._render_qweb_pdf(
                'reservation.report_reservation',
                self.ids,
                data=None
            )[0]

            report2 = self.env['ir.actions.report']._render_qweb_pdf(
                'reservation.report_livraison',
                self.ids,
                data=None
            )[0]

            report3 = self.env['ir.actions.report']._render_qweb_pdf(
                'reservation.report_reservation_',
                self.ids,
                data=None
            )[0]

            # Fusion des PDF
            merger = PdfMerger()
            merger.append(BytesIO(report1))
            merger.append(BytesIO(report2))
            merger.append(BytesIO(report3))

            # Génération du PDF fusionné
            pdf_content = BytesIO()
            merger.write(pdf_content)
            merger.close()

            # Encodage pour téléchargement
            pdf_content_b64 = base64.b64encode(pdf_content.getvalue())

            # Création d'un attachment temporaire
            attachment = self.env['ir.attachment'].create({
                'name': f'Documents_Combines_{self.name}.pdf',
                'type': 'binary',
                'datas': pdf_content_b64,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf'
            })

            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
        except Exception as e:
            raise UserError(f"Erreur lors de la génération du PDF combiné: {str(e)}")

    def confirme_modifications(self):
        for record in self:
            if not record.reservation:
                raise UserError("Aucune réservation associée.")
            date_debut = record.date_heure_debut
            if record.changed_place == record.lieu_retour:
                date_fin = record.changed_hour + timedelta(hours=1)
            else:
                date_fin = record.changed_hour + timedelta(hours=3)

            conflit = self.env['reservation'].search([
                ('vehicule', '=', record.vehicule.id),
                ('status', '=', 'confirmee'),
                ('date_heure_debut', '<', date_fin),
                ('date_heure_fin', '>', date_debut),
                ('id', '!=', record.reservation.id)
            ])

            if conflit:
                record.write({'is_available': 'non', 'sous_total': 0})
                return {'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {'title': 'Vehicule None disponible',
                                   'message': 'Le véhicule n\'est pas disponible.',
                                   'type': 'danger'
                                   }
                        }

            if record.changed_place == record.lieu_retour and record.changed_hour == record.date_heure_fin:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Pas de modification détecté',
                        'message': 'Velliez effecteuer des changement et verifier la disponibilité pour confirmer.',
                        'type': 'danger'
                    }
                }
            if record.lieu_retour != record.changed_place:
                record.reservation.ancien_lieu = f"{record.reservation.depart_retour} (Modifié)"
                record.reservation.lieu_retour = record.changed_place

            if record.changed_hour < record.date_heure_fin:
                retour_avance = self.env['retour.avance'].create({
                    'reservation': record.reservation.id,
                    'date_retour_avance': record.changed_hour
                })
                record.reservation.date_retour_avance = record.changed_hour

            if record.changed_hour > record.date_heure_fin:
                total = 0
                jours_supplementaires = (
                                                record.changed_hour.date() - record.date_heure_debut.date()).days - record.nbr_jour_reservation
                total += record.prix_jour * jours_supplementaires
                if record.reservation.retour_tard == 0:
                    heure_debut = record.date_heure_debut.time()
                    heure_fin = record.changed_hour.time()
                    ecart = (datetime.combine(date.min, heure_fin) - datetime.combine(date.min,
                                                                                      heure_debut)).seconds / 3600.0

                    if heure_debut > heure_fin:
                        ecart = ecart - 24

                    supplements = self.env['supplements'].search([('valeur', '>', 0)])
                    retour_tard_value = 0

                    for supplement in supplements:
                        if ecart > supplement.reatrd:
                            if record.reservation.prix_jour_two > 0:
                                retour_tard_value = record.reservation.prix_jour_two * 2 / 3
                            else:
                                retour_tard_value = record.reservation.prix_jour * 2 / 3

                        record.sous_total += retour_tard_value
                        total += retour_tard_value
                supplements_value = 0

                heure_debut_float = self._convert_to_float(record.date_heure_debut + timedelta(hours=1))
                heure_fin_float = self._convert_to_float(record.changed_hour + timedelta(hours=1))

                supplements = self.env['supplements'].search([])

                for supplement in supplements:
                    if supplement.heure_debut_float <= heure_debut_float < supplement.heure_fin_float:
                        supplements_value += supplement.montant

                for supplement in supplements:
                    if supplement.heure_debut_float <= heure_fin_float < supplement.heure_fin_float:
                        supplements_value += supplement.montant
                if record.reservation.supplements < supplements_value:
                    record.sous_total += supplements_value - record.reservation.supplements
                    total += supplements_value - record.reservation.supplements

                prolongation = self.env['prolongation'].create({
                    'reservation': record.reservation.id,
                    'date_prolonge': record.changed_hour,
                    'stage': 'confirme',
                    'prix_prolongation_devise': total,
                    'nb_jour_prolonge': jours_supplementaires,
                    'nb_jour_prolonge_l': f"{jours_supplementaires} jours"

                })
                record.reservation.du_au_modifier = f"{record.reservation.du_au} (Modifié)"
                record.reservation.date_heure_fin = record.changed_hour

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Succès',
                    'message': 'Les modifications ont été effectuées avec succès.',
                    'type': 'success'
                }
            }

    @api.depends('date_heure_fin', 'lieu_retour', 'change_heure_retour')
    def changed_place_hour(self):
        for rec in self:
            rec.changed_hour = rec.date_heure_fin
            rec.changed_place = rec.lieu_retour

    ecart_a_paye = fields.Monetary(string='Montant ajouté', currency_field='currency_id',
                                   compute='_compute_ecart_paye', store=True)
    sb_ajout = fields.Boolean(string="Siege bebe")
    sb_total = fields.Float(string="siege bebe total", compute='_compute_sb_total', store=True)

    @api.depends('sb_ajout', 'nbr_jour_reservation')
    def _compute_sb_total(self):
        for record in self:
            if record.sb_ajout:
                option_siege_bebe = self.env['options'].search([('option_code', '=', 'S_BEBE_5')], limit=1)
                record.sb_total = option_siege_bebe.prix * record.nbr_jour_reservation if option_siege_bebe else 0
            else:
                record.sb_total = 0

    max_ajoute = fields.Boolean(string="Protection max")
    max_total = fields.Float(string="Protection max total", compute='_compute_max_total', store=True)
    max_caution = fields.Float(string="Caution max", compute='_compute_max_total', store=True)

    @api.depends('max_ajoute', 'nbr_jour_reservation')
    def _compute_max_total(self):
        for record in self:
            if record.max_ajoute and record.vehicule:
                option_max = self.env['options'].search([
                    ('option_code', 'ilike', 'MAX'),
                    ('categorie', '=', record.vehicule.categorie.id)
                ], limit=1)

                record.max_total = option_max.prix * record.nbr_jour_reservation - record.reservation.opt_protection_total if option_max else 0
                record.max_caution = option_max.caution if option_max else 0
            else:
                record.max_total = 0
                record.max_caution = 0

    standart_ajoute = fields.Boolean(string="Protection standart")
    standart_total = fields.Float(string="Protection standart total", compute='_compute_standart_total', store=True)
    standart_caution = fields.Float(string="Caution standart", compute='_compute_standart_total', store=True)

    @api.depends('standart_ajoute', 'nbr_jour_reservation')
    def _compute_standart_total(self):
        for record in self:
            if record.standart_ajoute and record.vehicule:
                option_standart = self.env['options'].search([
                    ('option_code', 'ilike', 'STANDART'),
                    ('categorie', '=', record.vehicule.categorie.id)
                ], limit=1)

                record.standart_total = option_standart.prix * record.nbr_jour_reservation - record.reservation.opt_protection_total if option_standart else 0
                record.standart_caution = option_standart.caution if option_standart else 0
            else:
                record.standart_total = 0
                record.standart_caution = 0

    nd_driver_ajoute = fields.Boolean(string="2eme conducteur")
    nd_driver_total = fields.Float(string="2eme conducteur total", compute='_compute_nd_driver_total', store=True)

    @api.depends('nd_driver_ajoute', 'nbr_jour_reservation')
    def _compute_nd_driver_total(self):
        for record in self:
            if record.nd_driver_ajoute:
                option_nd_driver = self.env['options'].search([('option_code', '=', 'ND_DRIVER')], limit=1)
                record.nd_driver_total = option_nd_driver.prix * record.nbr_jour_reservation if option_nd_driver else 0
            else:
                record.nd_driver_total = 0

    carburant_ajoute = fields.Boolean(string="Carburant")
    carburant_total = fields.Boolean(string="Carburant total")
    carburant_total_f = fields.Float(string="Carburant total", compute='_compute_carburant_total', store=True)

    degradation_limit_euro = fields.Monetary(currency='currency_id', string='Degradation Limit',
                                             compute='_compute_limit_total', store=True)
    degradation_limit_da = fields.Monetary(currency='currency_da', string='Degradation Limit (DA)',
                                           compute='_compute_limit_total', store=True)

    @api.depends('total_eur', 'total_da')
    def _compute_limit_total(self):
        for record in self:
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            if record.total_eur > record.opt_protection_caution:
                record.degradation_limit_euro = record.opt_protection_caution
                record.degradation_limit_da = record.opt_protection_caution * taux_change.montant
            else:
                record.degradation_limit_euro = record.total_eur
                record.degradation_limit_da = record.total_da

    @api.depends('carburant_ajoute', 'nbr_jour_reservation')
    def _compute_carburant_total(self):
        for record in self:
            if record.carburant_ajoute:
                option_carburant = self.env['options'].search([('option_code', '=', 'P_CARBURANT')], limit=1)
                record.carburant_total_f = option_carburant.prix if option_carburant else 0
            else:
                record.carburant_total_f = 0

    total_supp = fields.Float(string="Total supplementaire", compute='compute_total_supp', store=True)

    @api.depends('carburant_total_f', 'nd_driver_total', 'standart_total', 'max_total', 'sb_total')
    def compute_total_supp(self):
        for record in self:
            record.total_supp = record.carburant_total_f + record.nd_driver_total + record.standart_total + record.max_total + record.sb_total

    total_payer = fields.Float(string="Total à payer", compute='compute_total_payer', store=True)

    @api.depends('total_supp', 'total_reduit_euro', 'total_eur', 'penalit_klm', 'sous_total', 'penalit_carburant')
    def compute_total_payer(self):
        for record in self:
            if record.lv_type == 'livraison':
                record.total_payer = record.total_reduit_euro + record.total_supp
            else:
                record.total_payer = record.total_reduit_euro + record.degradation_limit_euro + record.penalit_klm + record.penalit_carburant_euro

    def restitution_sans(self):
        template_id = self.env.ref('reservation.template_r_').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    montant_euro_pay = fields.Monetary(currency_field='currency_id', string='Montant €')
    montant_euro_ecart = fields.Monetary(currency_field='currency_id', string='Ecart €')
    montant_dz_pay = fields.Monetary(currency_field='currency_da', string='Montant DA')
    montant_dz_ecart = fields.Monetary(currency_field='currency_da', string='Ecart DA')
    total_payer_dz = fields.Monetary(currency_field='currency_da', string='Total à payer DA')

    def restitution(self):
        template_id = self.env.ref('reservation.template_restitutit').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_confiramion_livraison(self):
        # Récupérer l'ID du modèle d'email
        template_id = self.env.ref('reservation.template_confir', raise_if_not_found=False)
        if not template_id:
            raise UserError("Le modèle d'email 'reservation.template_confir' est introuvable. Veuillez vérifier.")

        # Récupérer l'ID du rapport
        report_id = self.env.ref('reservation_access.report_livraison', raise_if_not_found=False)
        if not report_id:
            raise UserError(
                "Le rapport 'reservation_access.report_livraison' est introuvable. Veuillez vérifier sa configuration.")

        for record in self:
            # Vérifier que l'adresse email existe
            if not record.email:
                raise UserError(f"L'adresse email est manquante pour {record.name}")

            # Générer le fichier PDF
            try:
                pdf_content, content_type = report_id._render_qweb_pdf([record.id])
            except Exception as e:
                raise UserError(f"Erreur lors de la génération du PDF : {e}")

            pdf_base64 = base64.b64encode(pdf_content)

            # Créer une pièce jointe pour le PDF
            attachment = self.env['ir.attachment'].create({
                'name': f'Confirmation_Livraison_{record.name}.pdf',
                'type': 'binary',
                'datas': pdf_base64,
                'res_model': self._name,
                'res_id': record.id,
                'mimetype': 'application/pdf',
            })

            # Envoyer l'email avec la pièce jointe
            template = self.env['mail.template'].browse(template_id.id)
            if template:
                mail_id = template.send_mail(record.id, force_send=False)
                mail = self.env['mail.mail'].browse(mail_id)
                mail.attachment_ids = [(4, attachment.id)]  # Ajouter l'attachement
                mail.send()  # Envoyer l'email
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def action_send_email_livraison(self):
        template_id = self.env.ref('email_confirmation_livraison').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    @api.depends('total_rduit_one', 'total_reduit_euro')
    def _compute_ecart_paye(self):
        for record in self:
            if record.total_reduit_euro:
                record.ecart_a_paye = record.total_reduit_euro - record.total_rduit_one

    @api.depends('lv_type', 'date_heure_debut', 'date_heure_fin', 'lieu_retour.name', 'lieu_depart.name')
    def _compute_action_date(self):
        for record in self:
            if record.lv_type == 'livraison':
                record.action_date = record.date_heure_debut
                record.action_lieu = record.lieu_depart.name
                record.color = 10
            else:
                record.action_date = record.date_heure_fin
                record.action_lieu = record.lieu_retour.name
                record.color = 2

    @api.depends('total_eur', 'total_prolone')
    def _compute_total_restitution_eur(self):
        for record in self:
            record.total_restitution_eur = record.total_eur + record.total_prolone

    @api.depends('degradation.prix')
    def _compute_total_da(self):
        for record in self:
            total = sum(degradation.prix for degradation in record.degradation)
            record.total_da = total

    @api.depends('degradation.prix_eur', 'total_da')
    def _compute_total_eur(self):
        for record in self:
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            differance = record.total_da / taux_change.montant
            record.total_eur = record.total_da / taux_change.montant

    @api.depends('total', 'total_prolone', 'caution_classic')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.total
            record.total_prolone_eur = record.total_prolone
            record.caution_classic_eur = record.caution_classic

    def action_open_revenue_popup(self):
        # Define default values for the new record
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Revenue Record',
            'view_mode': 'form',
            'res_model': 'revenue.record',
            'target': 'new',
            'context': {
                'default_reservation': self.reservation.id,
            }
        }

    def action_set_livre(self):
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
                elif record.nd_client_nom:
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
                    if client_existant and client_existant.risque == 'eleve':
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': 'Client Bloqué',
                                'message': 'Le client est bloqué vous ne pouvez pas l\'ajouter à cette reservation.',
                                'type': 'danger'
                            }
                        }
                    elif client_existant and client_existant.risque != 'eleve':
                        record.reservation.nd_client = client_existant
                    elif not client_existant:
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
                record.carburant_total_f = 0

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

            if record.total_payer > 10:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Paiement",
                        'message': "Vous ne pouvez pas valider cette action ",
                        'type': 'Danger',
                        'sticky': True,
                    }
                }
            if record.action_date and record.action_date.date() != (datetime.today() + timedelta(hours=1)).date():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Alerte",
                        'message': "Vous ne pouvez pas valider cette action car la date n'est pas celle d'aujourd'hui.",
                        'type': 'warning',
                        'sticky': True,
                    }
                }
            if not record.document_fournis or not record.etat_carburant or record.kilomtrage <= record.dernier_klm or not record.garantie:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Alerte",
                        'message': "Veuillez remplir les champs 'État carburant', 'Document fournis' et 'Caution "
                                   "déposé' avant de valider et remplir le kilométrage actuel du véhicule.",
                        'type': 'warning',
                        'sticky': True,
                    }
                }

            if record.kilomtrage > record.dernier_klm:
                record.vehicule.write({'dernier_klm': record.kilomtrage})

            record.stage = 'livre'
            record.livrer_par = self.env.user
            record.reservation.etat_reservation = 'loue'
            record.reservation.color_tag = 10
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Vehicule Livré",
                    'message': "Livraison effectuer avec succée.",
                    'type': 'success',
                    'sticky': True,
                }
            }

    def action_set_livre_r(self):
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
                elif record.nd_client_nom:
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
                    if client_existant and client_existant.risque == 'eleve':
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': 'Client Bloqué',
                                'message': 'Le client est bloqué vous ne pouvez pas l\'ajouter à cette reservation.',
                                'type': 'danger'
                            }
                        }
                    elif client_existant and client_existant.risque != 'eleve':
                        record.reservation.nd_client = client_existant
                    elif not client_existant:
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
                record.carburant_total_f = 0

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

            if record.total_payer > 10:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Paiement",
                        'message': "Vous ne pouvez pas valider cette action ",
                        'type': 'Danger',
                        'sticky': True,
                    }
                }
            if record.action_date and record.action_date.date() != (datetime.today() + timedelta(hours=1)).date():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Alerte",
                        'message': "Vous ne pouvez pas valider cette action car la date n'est pas celle d'aujourd'hui.",
                        'type': 'warning',
                        'sticky': True,
                    }
                }
            if record.kilomtrage < record.dernier_klm:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Alerte",
                        'message': "Veuillez remplir  le kilometrage actuele du véhicule",
                        'type': 'warning',
                        'sticky': True,
                    }
                }

            if record.kilomtrage >= record.dernier_klm:
                record.vehicule.write({'dernier_klm': record.kilomtrage})
            record.stage = 'livre'
            record.livrer_par = self.env.user

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Vehicule Livré",
                    'message': "Restitution effectuer avec succée.",
                    'type': 'success',
                    'sticky': True,
                }
            }

    @api.constrains('kilomtrage')
    def _check_kilomtrage(self):
        for record in self:
            if record.kilomtrage < record.dernier_klm:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Alerte",
                        'message': f"Le kilométrage ({record.kilomtrage}) ne doit pas être inférieur au dernier kilométrage ({record.dernier_klm}).",
                        'type': 'warning',
                        'sticky': True,
                    }
                }

    def write(self, vals):
        if 'kilomtrage' in vals:
            for record in self:
                new_kilomtrage = vals['kilomtrage']
                if new_kilomtrage < record.dernier_klm:
                    raise ValidationError(
                        f"Le kilométrage ({new_kilomtrage}) ne doit pas être inférieur au dernier kilométrage ({record.dernier_klm})."
                    )
        return super(Livraison, self).write(vals)

    @api.depends('reservation', 'lv_type')
    def _onchange_generate_name(self):
        if self.reservation and self.lv_type:
            self.name = f"{self.reservation.name} - {self.lv_type}"

    @api.model
    def create(self, vals):

        if 'reservation' in vals:
            reservation = self.env['reservation'].browse(vals['reservation'])
            if reservation.nd_conducteur == 'oui':
                vals['nd_condicteur'] = True

            if 3 in reservation.options.ids:
                vals['siege_bebe'] = True

            if 9 in reservation.options.ids:
                vals['plein_carburant'] = True

        return super(Livraison, self).create(vals)

    def siege_bebe_lv(self):
        self.siege_bebe = True
        self.reservation.options = [(4, 3)]

    def no_siege_bebe_lv(self):
        self.siege_bebe = False
        self.reservation.options = [(3, 3)]

    def plein_carburant_lv(self):
        self.plein_carburant = True
        self.reservation.options = [(4, 9)]

    def plein_complementaire_lv(self):
        self.assurance_complementaire = True
        if self.categorie.name == 'Categorie A':
            self.reservation.options = [(4, 11)]
        elif self.categorie == 'Catégorie B':
            self.reservation.options = [(4, 12)]
        elif self.categorie == 'Catégorie C':
            self.reservation.options = [(4, 13)]

    def no_plein_carburant_lv(self):
        self.plein_carburant = False
        self.reservation.options = [(3, 9)]

    def no_complementaire_lv(self):
        self.assurance_complementaire = False
        self.reservation.options = [(3, 11)]
        self.reservation.options = [(3, 12)]
        self.reservation.options = [(3, 13)]

    def action_open_liste_client_popup(self):
        reservation = self.reservation
        self.reservation.options = [(4, 8)]
        self.reservation.nd_conducteur_two = 'oui'
        return {
            'name': 'Ajouter Client',
            'view_mode': 'form',
            'res_model': 'liste.client',
            'view_id': self.env.ref('reservation.view_liste_client_form_pop_up').id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {
                'default_nd_condicteur': True,
                'default_livraison_id': self.id,
                'default_civilite': reservation.civilite_nd_condicteur,
                'default_nom': reservation.nom_nd_condicteur,
                'default_prenom': reservation.prenom_nd_condicteur,
                'default_email': reservation.email_nd_condicteur,
                'default_date_de_naissance': reservation.date_nd_condicteur,
                'default_date_de_permis': reservation.date_de_permis,

            }
        }


class ListClientInherit(models.Model):
    _inherit = 'liste.client'

    @api.model
    def create(self, vals):
        res = super(ListClientInherit, self).create(vals)
        livraison_id = self.env.context.get('default_livraison_id')
        if livraison_id:
            livraison = self.env['livraison'].browse(livraison_id)
            reservation = livraison.reservation
            reservation.update({
                'civilite_nd_condicteur': res.civilite,
                'nom_nd_condicteur': res.nom,
                'prenom_nd_condicteur': res.prenom,
                'email_nd_condicteur': res.email,
                'date_nd_condicteur': res.date_de_naissance,
                'date_de_permis': res.date_de_permis,

            })
            livraison.nd_condicteur = True
        return res

    @api.depends('civilite', 'nom', 'prenom')
    def _compute_full_name(self):
        for record in self:
            record.name = ' '.join(filter(None, [record.civilite, record.nom, record.prenom]))
