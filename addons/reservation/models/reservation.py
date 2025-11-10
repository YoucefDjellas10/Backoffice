from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import random
import string
import logging
import requests
from dateutil.relativedelta import relativedelta
_logger = logging.getLogger(__name__)


class Reservation(models.Model):
    _name = 'reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'reservation des vehicules'

    name = fields.Char(string='Référence', readonly=True, default=lambda self: self._generate_unique_code_(),
                       unique=True)
    status = fields.Selection([('en_attend', 'En attend'),
                               ('rejete', 'Rejeté'),
                               ('annule', 'Annulé'),
                               ('confirmee', 'Confirmé')], string='Etat confirmation', default='confirmee')
    etat_reservation = fields.Selection([('reserve', 'Réservé'),
                                         ('loue', 'Loué'),
                                         ('annule', 'Annulé')], string='Etat reservation', default='reserve')
    date_heure_debut = fields.Datetime(string='Date heure debut', required=True,
                                       default=lambda self: fields.Datetime.now())
    date_heure_debut_format = fields.Char(string='Date heure debut',
                                          compute='_compute_date_heure_debut_format')
        
    create_date_trimmed = fields.Char(
        string="Date",
        store=False
    )

    def download__combined_documents(self):
        """Télécharge les documents combinés"""
        url = f"https://api.safarelamir.com/combined-document-download/?reservation_id={self.id}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',  # Ouvre dans un nouvel onglet
        }

    def _compute_create_date_trimmed(self):
        for record in self:
            if record.create_date:
                record.create_date_trimmed = record.create_date.strftime('%d/%m/%Y %H:%M')



    @api.model
    def _cron_clean_duplicate_reservations(self, limit=300):
        """
        Nettoyage progressif et doux des doublons de réservations.
        Traite les doublons (name + client) par petits lots pour ne pas saturer la mémoire.
        """
        _logger.info("🚀 [CRON Doux] Démarrage du nettoyage des doublons de réservations (par lot de %s)...", limit)

        # Trouver les combinaisons (name, client) qui ont plus d'une occurrence
        self.env.cr.execute("""
            SELECT name, client
            FROM reservation
            WHERE client IS NOT NULL AND name IS NOT NULL
            GROUP BY name, client
            HAVING COUNT(*) > 1
            LIMIT %s
        """, (limit,))
        duplicates = self.env.cr.fetchall()

        if not duplicates:
            _logger.info("✅ Aucun doublon détecté dans cette passe.")
            return

        total_deleted = 0

        for name, client_id in duplicates:
            records = self.search([('name', '=', name), ('client', '=', client_id)])
            if len(records) < 2:
                continue

            rec_with_livraison = records.filtered(lambda r: len(r.livraison) > 0)
            rec_without_livraison = records.filtered(lambda r: len(r.livraison) == 0)

            record_to_delete = False

            if len(rec_with_livraison) == 1 and len(rec_without_livraison) >= 1:
                record_to_delete = rec_without_livraison[0]
            elif len(rec_with_livraison) == 0 or len(rec_with_livraison) == len(records):
                record_to_delete = records.sorted(lambda r: r.create_date)[0]
            else:
                record_to_delete = records[0]

            if record_to_delete:
                try:
                    _logger.info("🗑️ Suppression du doublon ID %s (client=%s, name=%s)", record_to_delete.id, client_id, name)
                    record_to_delete.unlink()
                    total_deleted += 1
                except Exception as e:
                    _logger.warning("❌ Erreur suppression %s: %s", record_to_delete.id, e)

            # ✅ Libération mémoire (important avec 29k records)
            self.env.clear()

        _logger.info("💤 Nettoyage partiel terminé. %s doublon(s) supprimé(s) dans cette passe.", total_deleted)
        _logger.info("🕒 Le prochain cron continuera le traitement automatiquement.")

    @api.model
    def cron_update_annule_records(self):
        """
        Met à jour les réservations : si status == 'annule' alors etat_reservation = 'annule'
        Optimisée pour traiter de grands volumes (> 20k lignes).
        """
        _logger.info("=== Début cron_update_annule_records ===")

        # Exécution SQL directe pour éviter de charger tous les enregistrements
        query = """
            UPDATE reservation
            SET etat_reservation = 'annule'
            WHERE status = 'annule'
              AND (etat_reservation IS DISTINCT FROM 'annule');
        """
        self.env.cr.execute(query)
        self.env.cr.commit()

        _logger.info("=== Fin cron_update_annule_records ===")


    @api.model
    def cron_update_reservations_to_loue(self):
        """Cron pour passer les réservations confirmées à 'loué',
        mettre à jour la livraison et créer le revenu si reste_payer > 20."""
        
        # Date limite
        date_limite = datetime(2025, 10, 25)

        # On récupère toutes les réservations concernées
        reservations = self.search([
            ('status', '=', 'confirmee'),
            ('etat_reservation', '!=', 'loue'),
            ('date_heure_debut', '<', date_limite)
        ])

        if not reservations:
            return

        _logger.info(f"CRON: {len(reservations)} réservations trouvées pour mise à jour en 'loué'.")

        # Précharger les livraisons en une seule requête
        livraisons = self.env['livraison'].search([
            ('reservation', 'in', reservations.ids),
            ('lv_type', '=', 'livraison')
        ])

        # Mapping reservation_id -> livraison record
        livraison_map = {l.reservation.id: l for l in livraisons}

        revenues_to_create = []

        for reservation in reservations:
            # 1. Mise à jour du statut
            reservation.etat_reservation = 'loue'

            # 2. Mettre à jour la livraison liée
            livraison = livraison_map.get(reservation.id)
            if livraison:
                livraison.stage = 'livre'
                # On vérifie que le champ existe avant d’écrire
                if hasattr(livraison, 'date_de_livraison'):
                    livraison.date_de_livraison = reservation.date_heure_debut

            # 3. Créer un revenue.record si reste_payer > 20
            if reservation.reste_payer and reservation.reste_payer > 20:
                revenues_to_create.append({
                    'reservation': reservation.id,
                    'montant': reservation.reste_payer,
                    'mode_paiement': 'liquide',
                })

        # Création en masse des records revenue.record
        if revenues_to_create:
            self.env['revenue.record'].create(revenues_to_create)
            _logger.info(f"CRON: {len(revenues_to_create)} revenus créés pour les réservations louées.")

        _logger.info("CRON terminé : mise à jour des réservations et livraisons effectuée avec succès.")

    def action_adjust_create_date(self):
        for record in self:
            if record.create_date:
                record.create_date_trimmed = record.create_date.strftime('%d/%m/%Y %H:%M')
        return True


    def _compute_date_heure_debut_format(self):
        for record in self:
            if record.date_heure_debut:
                record.date_heure_debut_format = record.date_heure_debut.strftime('%d-%m-%Y %H:%M')

    date_heure_fin = fields.Datetime(string='Date heure fin', required=True,
                                     default=lambda self: fields.Datetime.now() + timedelta(days=3))
    date_heure_fin_format = fields.Char(string='Date heure fin', compute='_compute_date_heure_format')

    def _compute_date_heure_format(self):
        for record in self:
            if record.date_heure_debut:
                record.date_heure_debut_format = record.date_heure_debut.strftime('%Y-%m-%d %H:%M')
            if record.date_heure_fin:
                record.date_heure_fin_format = record.date_heure_fin.strftime('%d-%m-%Y %H:%M')

    nbr_jour_reservation = fields.Integer(string='Durée', readonly=True, store=True)

    duree_dereservation = fields.Char(string='Durée', compute='_compute_duree_dereservation', store=True)
    exchange_amount = fields.Float(string='change')
    num_vol = fields.Char()
    lieu_depart = fields.Many2one('lieux', string='Lieu de départ', required=True)
    numero_lieu = fields.Char(string='Numero lieu', related='lieu_depart.mobile', store=True)
    zone = fields.Many2one(string='Zone de depart', related='lieu_depart.zone', store=True)
    address_fr = fields.Char(string='Adresse FR', related='lieu_depart.address', store=True)
    address_en = fields.Char(string='Adresse EN', related='lieu_depart.address_en', store=True)
    address_ar = fields.Char(string='Adresse AR', related='lieu_depart.address_ar', store=True)
    lieu_retour = fields.Many2one('lieux', string='Lieu de retour', domain="[('zone', '=', zone)]", required=True)
    vehicule = fields.Many2one('vehicule', string='Véhicule', domain="[('zone', '=', zone)]")
    modele = fields.Many2one(string='Modele', related='vehicule.modele', store=True)
    categorie = fields.Many2one(string='categorie', related='vehicule.categorie', store=True)
    carburant = fields.Selection(string='Carburant', related='vehicule.carburant', store=True)

    model_name = fields.Char(string='model name', related='vehicule.model_name', store=True)
    marketing_text_fr = fields.Char(string='marketing text fr', related='vehicule.marketing_text_fr', store=True)
    photo_link = fields.Char(string='photo link ', related='vehicule.photo_link', store=True)
    photo_link_nd = fields.Char(string='photo link_nd', related='vehicule.photo_link_nd', store=True)
    nombre_deplace = fields.Char(string='nombre deplace', related='vehicule.nombre_deplace', store=True)
    nombre_de_porte = fields.Char(string='nombre de porte', related='vehicule.nombre_de_porte', store=True)
    nombre_de_bagage = fields.Char(string='nombre de bagage', related='vehicule.nombre_de_bagage', store=True)
    boite_vitesse = fields.Selection(string='boite vitesse', related='vehicule.boite_vitesse', store=True)
    age_min = fields.Char(string='Carburant', related='vehicule.age_min', store=True)
    start = fields.Boolean()

    date_debut_service = fields.Date(string='Date mis en service', related='vehicule.date_debut_service', store=True)
    date_fin_service = fields.Date(string='Date fin de service', related='vehicule.date_fin_service', store=True)
    matricule = fields.Char(string='Matricule', related='vehicule.matricule', store=True)
    numero = fields.Char(string='Numéro', related='vehicule.numero', store=True)

    client = fields.Many2one('liste.client', string='Client', required=True)
    client_create_date = fields.Datetime(string='Client Create Date', related='client.create_date', store=True)
    nom = fields.Char(string='Nom', related='client.nom', store=True)
    prenom = fields.Char(string='Prénom', related='client.prenom', store=True)
    email = fields.Char(string='Email', related='client.email', store=True)
    date_de_naissance = fields.Date(string='Date de naissance', related='client.date_de_naissance', store=True)
    permis_date = fields.Date(string='Date permis', related='client.date_de_permis', store=True)
    mobile = fields.Char(string='Mobile', related='client.mobile', store=True)
    
    date_depart_char = fields.Char(string='date depart')
    date_retour_char = fields.Char(string='date retour')
    heure_depart_char = fields.Char(string='heure depart')
    heure_retour_char = fields.Char(string='heure retour')
    lecart = fields.Float(string='L\'écart', help="Le montant saisi sera ajouté au total (+).")

    @api.model
    def _cron_update_exchange_amount(self):
        date_limite = datetime(2025, 9, 30, 23, 59, 59)
        date_fin_octobre = datetime(2025, 10, 31, 23, 59, 59)
        reservations = self.search([
            ('create_date', '>', date_limite)
        ])
        for reservation in reservations:
            create_date = fields.Datetime.from_string(reservation.create_date)
            if create_date <= date_fin_octobre:
                reservation.exchange_amount = 250
            else:
                reservation.exchange_amount = 260
        return True

    @api.model
    def cron_verify_recent_reservations(self):
        """
        Vérifie et corrige les réservations créées dans la dernière heure :
        1. Recalcule et corrige le reste_payer si nécessaire
        2. Corrige les dates/heures à partir des champs char
        """
        _logger.info("=== Début de la vérification des réservations récentes ===")

        # Calculer l'heure limite (il y a 1 heure)
        one_hour_ago = fields.Datetime.now() - timedelta(hours=7000)

        # Rechercher les réservations créées dans la dernière heure
        recent_reservations = self.search([
            ('create_date', '>=', one_hour_ago)
        ])

        if not recent_reservations:
            _logger.info("Aucune réservation récente trouvée")
            return True

        _logger.info(f"Traitement de {len(recent_reservations)} réservation(s) récente(s)")

        corrections_revenue = 0
        corrections_refunds = 0
        corrections_reste_payer = 0
        corrections_dates = 0
        erreurs = []

        for reservation in recent_reservations:
            try:
                try:
                    
                    
                    if reservation.exchange_amount and reservation.exchange_amount > 0:
                        total_revenue_calcule = (
                                sum(reservation.revenue_ids.mapped('montant')) +
                                sum(reservation.revenue_ids.mapped('montant_dzd')) / reservation.exchange_amount
                        )
                    else:
                        # Si pas de taux de change, calculer sans conversion DZD
                        total_revenue_calcule = sum(reservation.revenue_ids.mapped('montant'))
                        if not reservation.exchange_amount:
                            _logger.warning(
                                f"Réservation {reservation.name}: taux de change ID=2 introuvable"
                            )

                    # Comparer avec tolérance de 0.01
                    if abs(reservation.total_revenue - total_revenue_calcule) > 0.01:
                        _logger.warning(
                            f"Réservation {reservation.name} (ID: {reservation.id}): "
                            f"total_revenue incorrect {reservation.total_revenue} → {total_revenue_calcule}"
                        )
                        reservation.write({'total_revenue': total_revenue_calcule})
                        corrections_revenue += 1

                except Exception as e:
                    erreurs.append(
                        f"Réservation {reservation.name} - Erreur calcul total_revenue: {e}"
                    )
                    _logger.exception(f"Erreur calcul total_revenue pour réservation {reservation.id}")

                    # ===== 2. VÉRIFICATION DU TOTAL_REFUNDS =====
                try:
                    refunds_effectues = reservation.refunds_ids.filtered(
                        lambda r: r.status == 'effectuer'
                    )
                    total_refunds_calcule = sum(refunds_effectues.mapped('amount'))

                    # Comparer avec tolérance de 0.01
                    if abs(reservation.total_refunds - total_refunds_calcule) > 0.01:
                        _logger.warning(
                            f"Réservation {reservation.name} (ID: {reservation.id}): "
                            f"total_refunds incorrect {reservation.total_refunds} → {total_refunds_calcule}"
                        )
                        reservation.write({'total_refunds': total_refunds_calcule})
                        corrections_refunds += 1

                except Exception as e:
                    erreurs.append(
                        f"Réservation {reservation.name} - Erreur calcul total_refunds: {e}"
                    )
                    _logger.exception(f"Erreur calcul total_refunds pour réservation {reservation.id}")

                    # Rafraîchir les valeurs après les éventuelles corrections
                


                # ===== 1. VÉRIFICATION DU RESTE À PAYER =====
                reste_payer_calcule = (
                        reservation.total_reduit_euro +
                        reservation.total_degrader +
                        reservation.total_ecce_klm -
                        reservation.total_revenue +
                        reservation.total_refunds
                )

                # Comparer avec une tolérance de 0.01 pour éviter les erreurs de float
                if abs(reservation.reste_payer - reste_payer_calcule) > 0.01:
                    _logger.warning(
                        f"Réservation {reservation.name} (ID: {reservation.id}): "
                        f"reste_payer incorrect {reservation.reste_payer} → {reste_payer_calcule}"
                    )
                    reservation.write({'reste_payer': reste_payer_calcule})
                    corrections_reste_payer += 1

                # ===== 2. CORRECTION DES DATES/HEURES =====
                date_debut_corrigee = None
                date_fin_corrigee = None

                # Corriger date_heure_debut
                if reservation.date_depart_char and reservation.heure_depart_char:
                    try:
                        date_debut_corrigee = self._parse_date_heure(
                            reservation.date_depart_char,
                            reservation.heure_depart_char
                        )
                    except Exception as e:
                        erreurs.append(
                            f"Réservation {reservation.name} - Erreur parsing date début: {e}"
                        )

                # Corriger date_heure_fin
                if reservation.date_retour_char and reservation.heure_retour_char:
                    try:
                        date_fin_corrigee = self._parse_date_heure(
                            reservation.date_retour_char,
                            reservation.heure_retour_char
                        )
                    except Exception as e:
                        erreurs.append(
                            f"Réservation {reservation.name} - Erreur parsing date fin: {e}"
                        )

                # Appliquer les corrections si nécessaires
                vals_to_write = {}

                if date_debut_corrigee:
                    date_debut_actuelle = fields.Datetime.from_string(reservation.date_heure_debut)
                    # Vérifier si décalage > 30 minutes (pour éviter corrections inutiles)
                    if abs((date_debut_corrigee - date_debut_actuelle).total_seconds()) > 1800:
                        vals_to_write['date_heure_debut'] = fields.Datetime.to_string(date_debut_corrigee)
                        _logger.info(
                            f"Réservation {reservation.name}: date_heure_debut corrigée "
                            f"{date_debut_actuelle} → {date_debut_corrigee}"
                        )

                if date_fin_corrigee:
                    date_fin_actuelle = fields.Datetime.from_string(reservation.date_heure_fin)
                    if abs((date_fin_corrigee - date_fin_actuelle).total_seconds()) > 1800:
                        vals_to_write['date_heure_fin'] = fields.Datetime.to_string(date_fin_corrigee)
                        _logger.info(
                            f"Réservation {reservation.name}: date_heure_fin corrigée "
                            f"{date_fin_actuelle} → {date_fin_corrigee}"
                        )

                if vals_to_write:
                    reservation.write(vals_to_write)
                    corrections_dates += 1

            except Exception as e:
                erreurs.append(f"Réservation {reservation.name} (ID: {reservation.id}): {str(e)}")
                _logger.exception(f"Erreur lors du traitement de la réservation {reservation.id}")

        # Rapport final
        _logger.info("=== Fin de la vérification ===")
        _logger.info(f"Réservations traitées: {len(recent_reservations)}")
        _logger.info(f"Corrections reste_payer: {corrections_reste_payer}")
        _logger.info(f"Corrections dates/heures: {corrections_dates}")

        if erreurs:
            _logger.warning(f"Erreurs rencontrées ({len(erreurs)}):")
            for erreur in erreurs:
                _logger.warning(f"  - {erreur}")

        return True

    def _parse_date_heure(self, date_char, heure_char):
        """
        Convertit date_char (JJ/MM/YYYY ou YYYY-MM-DD) + heure_char (HH:MM)
        en datetime Python en tenant compte du timezone Africa/Algiers
        """
        import pytz

        # Nettoyer les espaces
        date_char = date_char.strip() if date_char else ''
        heure_char = heure_char.strip() if heure_char else '00:00'

        if not date_char:
            raise ValueError("Date vide")

        # Essayer différents formats de date
        date_obj = None
        for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
            try:
                date_obj = datetime.strptime(date_char, fmt).date()
                break
            except ValueError:
                continue

        if not date_obj:
            raise ValueError(f"Format de date non reconnu: {date_char}")

        # Parser l'heure
        try:
            heure_obj = datetime.strptime(heure_char, '%H:%M').time()
        except ValueError:
            # Si format invalide, utiliser 00:00
            _logger.warning(f"Format d'heure invalide: {heure_char}, utilisation de 00:00")
            heure_obj = datetime.strptime('00:00', '%H:%M').time()

        # Combiner date + heure (datetime naïf)
        datetime_combine = datetime.combine(date_obj, heure_obj)

        # Localiser dans le timezone Algeria (Africa/Algiers)
        tz_algiers = pytz.timezone('Africa/Algiers')
        datetime_local = tz_algiers.localize(datetime_combine)

        # Convertir en UTC (ce qu'Odoo attend)
        datetime_utc = datetime_local.astimezone(pytz.UTC)

        # Retourner sans timezone info (Odoo préfère les datetime naïfs en UTC)
        return datetime_utc.replace(tzinfo=None)

    def confirmer_lecart(self):
        for record in self:
            params = {
                'reservation_id': record.id if record.id else '',
                'montant': record.lecart if record.lecart else 0,
            }

            url = "https://api.safarelamir.com/ajouter-ecart/"
            try:
                response = requests.get(url, params=params, timeout=20)
                if response.status_code == 200:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Erreur',
                            'message': f"Un problème est survenu (status: {response.status_code})",
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
                        'message': f"Erreur lors de l'appel API: {str(e)}",
                        'type': 'danger',
                        'sticky': True,
                    }
                }


    def action_ouvrir_ecart_pop_up(self):
        return {
            'name': 'Ajouter un écart',
            'type': 'ir.actions.act_window',
            'res_model': 'reservation',
            'view_mode': 'form',
            'view_id': self.env.ref('reservation.view_liste_ajouter_ecart_pop_up').id,
            'res_id': self.id,
            'target': 'new',  
            'context': {
                'default_lecart': self.lecart, 
            }
        } 

    def confirmer_l_annulation(self):
        for record in self:
            params = {
                'reservation_id': record.id if record.id else '',
                'motif': record.annuler_raison.id if record.annuler_raison.id else ''
            }

            url = "https://api.safarelamir.com/cancel-from-system/"
            try:
                response = requests.get(url, params=params, timeout=20)
                if response.status_code == 200:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Erreur',
                            'message': f"Un problème est survenu (status: {response.status_code})",
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
                        'message': f"Erreur lors de l'appel API: {str(e)}",
                        'type': 'danger',
                        'sticky': True,
                    }
                }

    def action_annuler_request_pop_up(self):
        return {
            'name': 'Anuler la réservation',
            'type': 'ir.actions.act_window',
            'res_model': 'reservation',
            'view_mode': 'form',
            'view_id': self.env.ref('reservation._view_annuler_reservation_pop_up').id,
            'res_id': self.id,
            'target': 'new',

        }


    telephone = fields.Char(string='Téléphone', related='client.telephone', store=True)
    risque = fields.Selection(string='Risque', related='client.risque', store=True)
    note = fields.Text(string='Note', related='client.note', store=True)
    categorie_client = fields.Many2one(string='Categorie', related='client.categorie_client', store=True)
    options_gratuit = fields.Many2many('options', string='Options Gratuites',
                                       related='client.options_gratuit')
    code_prime = fields.Char(string='Code Prime', related='client.code_prime', store=True, readonly=True)
    reduction = fields.Integer(string='Réduction %', related='client.reduction', store=True)
    devise = fields.Many2one(string='Devise', related='client.devise', store=True)
    solde = fields.Monetary(string='Solde non consomé', currency_field='devise', related='client.solde', store=True)
    solde_total = fields.Integer(string='Solde Total', related='client.solde_total', store=True)
    solde_consomer = fields.Integer(string='Solde consomé', related='client.solde_consomer', store=True)

    nd_client = fields.Many2one('liste.client', string=' Deuxieme Client')
    nom_nd = fields.Char(string='Nom', related='nd_client.nom', store=True)
    prenom_nd = fields.Char(string='Prénom', related='nd_client.prenom', store=True)
    email_nd = fields.Char(string='Email', related='nd_client.email', store=True)
    date_de_naissance_nd = fields.Date(string='Date de naissance', related='nd_client.date_de_naissance', store=True)
    permis_date_nd = fields.Date(string='Date permis', related='nd_client.date_de_permis', store=True)
    mobile_nd = fields.Char(string='Mobile', related='nd_client.mobile', store=True)

    telephone_nd = fields.Char(string='Téléphone', related='nd_client.telephone', store=True)
    risque_nd = fields.Selection(string='Risque', related='nd_client.risque', store=True)
    note_nd = fields.Text(string='Note', related='nd_client.note', store=True)
    categorie_client_nd = fields.Many2one(string='Categorie', related='nd_client.categorie_client', store=True)
    options_gratuit_nd = fields.Many2many('options', string='Options Gratuites',
                                       related='nd_client.options_gratuit')

    confirmation_date = fields.Datetime(string='Date de confitmation')
    cancelation_date = fields.Datetime(string='Date d\'annulation')


    code_prime_nd = fields.Char(string='Code Prime', related='nd_client.code_prime', store=True, readonly=True)
    reduction_nd = fields.Integer(string='Réduction %', related='nd_client.reduction', store=True)
    devise_nd = fields.Many2one(string='Devise', related='nd_client.devise', store=True)
    solde_nd = fields.Monetary(string='Solde non consomé', currency_field='devise', related='nd_client.solde', store=True)

    def action_confirmer_reservation(self):
        for record in self:
            if not record.id:
                raise UserError(_("Impossible de confirmer : la réservation n'a pas d'identifiant."))

            url = f"https://api.safarelamir.com/confirmer-resrevation/?reservation_id={record.id}"

            try:
                response = requests.get(url, timeout=20)
            except Exception as e:
                raise UserError(_("Erreur de connexion avec l'API: %s") % str(e))

            if response.status_code == 200:
                data = response.json()
                if data.get("operation") == "operation terminé":
                    record.status = "confirmee"

                    # Notification succès
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Succès'),
                            'message': _('La réservation est confirmée avec succès !'),
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    raise UserError(_("L'API a répondu mais avec une erreur: %s") % data.get("operation"))
            else:
                raise UserError(
                    _("Échec de l'appel API. Code HTTP: %s - Réponse: %s") % (response.status_code, response.text))

    prix_jour = fields.Integer(string='Prix par jours', readonly=True, store=True)
    prix_jour_two = fields.Integer(string='Prix Jour Two')
    nbr_jour_two = fields.Integer(string='Nombre de Jours Two')
    nbr_jour_one = fields.Integer(string='Nombre de Jours One')
    frais_de_livraison = fields.Integer(string='Frais de livraison', readonly=True, store=True)
    options = fields.Many2many('options', string='Options', store=True, domain="[('id', '!=', 10)]")
    options_total = fields.Integer(string='Total des options', readonly=True, store=True)
    options_total_reduit = fields.Integer(string='Total options reduit', readonly=True,
                                          store=True)

    total = fields.Integer(string='Total Général', readonly=True, store=True)
    total_reduit = fields.Integer(string='Total Réduit', readonly=True, store=True)

    currency_id_reduit = fields.Many2one('res.currency', string='Currency',
                                         default=lambda self: self.env['res.currency'].browse(125).id)
    total_reduit_euro = fields.Monetary(string='Total Réduit (EUR)', currency_field='currency_id_reduit',
                                         readonly=True, store=True)
    total_revenue = fields.Float()
    montant_paye = fields.Monetary(string='Montant Payé', compute="_compute_montant_paye", store=True,
                                   currency_field='currency_id_reduit')
    reste_payer = fields.Monetary(string='Reste à Payer', compute="_compute_reste_payer", store=True,
                                  currency_field='currency_id_reduit')
    total_degrader = fields.Monetary(string='Total des dégradation', currency_field='currency_id_reduit')
    total_ecce_klm = fields.Monetary(string='Total KM non respecté', currency_field='currency_id_reduit')
    
    def action_create_edit_reservation(self):
        for record in self:
            if not record.date_heure_debut or not record.date_heure_fin:
                raise UserError("Les champs date_heure_debut et date_heure_fin doivent être renseignés.")
            date_depart = record.date_heure_debut.date()
            date_retour = record.date_heure_fin.date()

            edit_res = self.env['edit.reservation'].create({
                'date_depart': date_depart,
                'date_retour': date_retour,
                'heure_depart': record.heure_depart_char,
                'heure_retour': record.heure_retour_char,
                'reservation': record.id,
                'lieu_depart': record.lieu_depart.id if record.lieu_depart else False,
                'lieu_retour': record.lieu_retour.id if record.lieu_retour else False,
            })

            return {
                'type': 'ir.actions.act_window',
                'name': 'Modifier la réservation',
                'res_model': 'edit.reservation',
                'view_mode': 'form',
                'res_id': edit_res.id,
                'target': 'new',
                'context': {
                    'source_model': 'reservation',
                    'source_id': record.id,
                }
            }
   
    @api.depends('total_revenue')
    def _compute_montant_paye(self):
        for record in self:
            record.montant_paye = record.total_revenue

    total_refunds = fields.Monetary(
        string='Total des remboursements',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.ref('base.EUR').id)
    @api.depends('total_refunds','montant_paye', 'total_revenue', 'total_degrader', 'total_ecce_klm', 'date_heure_fin', 'date_heure_debut', 'total_reduit_euro')
    def _compute_reste_payer(self):
        for record in self:
            record.reste_payer = record.total_reduit_euro + record.total_degrader + record.total_ecce_klm - record.total_revenue + record.total_refunds


    du_au = fields.Char(string='Du ➝ Au', compute='_compute_du_au', store=True)
    du_au_modifier = fields.Char(string='Du ➝ Au (Modifié)')

    @api.depends('date_heure_debut', 'date_heure_fin')
    def _compute_du_au(self):
        for record in self:
            if record.date_heure_debut and record.date_heure_fin:
                date_debut_plus_one = record.date_heure_debut + timedelta(hours=1)
                date_fin_plus_one = record.date_heure_fin + timedelta(hours=1)
                record.du_au = f"{date_debut_plus_one.strftime('%d/%m/%Y %H:%M')} ➝ {date_fin_plus_one.strftime('%d/%m/%Y %H:%M')}"
            else:
                record.du_au = ''

    
    total_afficher = fields.Integer(string='Total Afficher', readonly=True, store=True)
    total_afficher_reduit = fields.Integer(string='Total Afficher reduit', readonly=True,
                                           store=True)
    prix_jour_afficher = fields.Float(string='Prix par jour Afficher',
                                      readonly=True, store=True)
    prix_jour_afficher_reduit = fields.Float(string='Prix par jour reduit',
                                             readonly=True, store=True)
    supplements = fields.Integer(string='Supplements', readonly=True, store=True)
    retour_tard = fields.Integer(string='Retour tard', readonly=True, store=True)
    livraison = fields.One2many('livraison', 'reservation', string='Livraison')
    kilometrage_depart = fields.Integer(string='Kilometrage', compute='_compute_kilometrage_depart', store=True)

    @api.depends('livraison.kilomtrage', 'livraison.lv_type')
    def _compute_kilometrage_depart(self):
        for record in self:
            livraison_liee = record.livraison.filtered(lambda l: l.lv_type == 'livraison')
            if livraison_liee:
                record.kilometrage_depart = livraison_liee[
                    0].kilomtrage  # Prend la première livraison avec lv_type 'livraison'
            else:
                record.kilometrage_depart = 0


    civilite_nd_condicteur = fields.Selection([('Mr', 'M.'), ('Mme', 'Mme'), ('Mlle', 'Mlle')], string='Civilité')
    nom_nd_condicteur = fields.Char(string='Nom')
    prenom_nd_condicteur = fields.Char(string='Prénom')
    email_nd_condicteur = fields.Char(string='Email')
    date_nd_condicteur = fields.Date(string='Date de naissance')
    date_de_permis = fields.Date(string='Date de permis')
    nd_conducteur = fields.Selection([('oui', 'oui'), ('non', 'non')], string='2eme condicteur', default='non')
    nd_conducteur_two = fields.Selection([('oui', 'oui'), ('non', 'non')], string='2eme condicteur two', default='non')

    is_nd_cond = fields.Boolean(string='existe nd condicteur', compute='_compute_is_nd_cond', store=True)

    client_created = fields.Boolean(string="Client créé", default=False)
    liste_client_id = fields.Many2one('liste.client', string='2ème chauffeur')
    note_lv_d = fields.Text(string='Note')
    note_lv_r = fields.Text(string='Note')
    annuler_raison = fields.Many2one('annuler.raison', string='raison d annulation')
    rejet_raison = fields.Many2one('reje.raison', string='raison de rejet')
    livrer_par = fields.Many2one('res.users', string='Livré par', compute='_compute_livrer_par', store=True)
    prolongation = fields.One2many('prolongation', 'reservation', string='Reservation')
    prolonge = fields.Selection([('non', 'Non'), ('oui', 'Oui')], string='Prolongé', default='non')
    total_prolone = fields.Integer(string='Total prolongé', compute='_compute_total_prolone', store=True)
    depart_retour = fields.Char(string='Départ ➝ retour', compute='_compute_depart_retour', store=True)
    depart_retour_ancien = fields.Char(string='Départ ➝ retour (Ancien)')
    frais_de_dossier = fields.Integer(string='Frais de dossier', readonly=True, store=True)
    retour_avance = fields.Boolean(string='Retour a l\' avance', default=False)
    date_retour_avance = fields.Datetime(string='Retour a l\'avance',default=lambda self: fields.Datetime.now() + timedelta(days=3))
    retour_avace_ids = fields.One2many('retour.avance', 'reservation', string='Retour à l avance')
    klm_moyen = fields.Char(string='Kilometrage moyen', compute='_compute_klm_moyen', store=True)
    klm_moyen_int = fields.Integer(string='Kilometrage moyen', compute='_compute_klm_moyen', store=True)
    color = fields.Char(compute='_compute_color', string='Color')
    color_tag = fields.Integer(string='Color')
    photo_depart = fields.Many2many('ir.attachment', string='Photos depart', compute='_compute_photo_depart')
    solde_reduit = fields.Integer(string='Ancien Solde')
    ancien_lieu = fields.Char(string='Ancien Lieux')

    def action_print_report(self):
        return self.env.ref('reservation_access.report_reservation').report_action(self)

    heure_prise = fields.Char(string="Heure de Prise", compute="_compute_heure_prise_retour")
    heure_retour = fields.Char(string="Heure de Retour", compute="_compute_heure_prise_retour")

    date_depart = fields.Date(string='Date depart', compute='_compute_dates', store=True)
    date_retour = fields.Date(string='Date retour', compute='_compute_dates', store=True)
    nombre_jours = fields.Integer(string='Nombre de jours', compute='_compute_nombre_jours', store=True)
    age_condicteur = fields.Integer(string='Âge du conducteur', compute='_compute_age_condicteur', store=True)

    opt_payment = fields.Many2one('options', string='paiement a la livraison')
    opt_payment_name = fields.Char(string='paiement a la livraison name', related='opt_payment.name', store=True)
    opt_payment_price = fields.Integer(string='paiement a la livraison name', related='opt_payment.prix', store=True)
    opt_payment_total = fields.Integer(string='Paiement a la livraison', compute='opt_payment_compute', store=True)

    @api.depends('opt_payment')
    def opt_payment_compute(self):
        for record in self:
            if record.opt_payment.type_tarif == 'fixe':
                record.opt_payment_total = record.opt_payment.prix
            else:
                record.opt_payment_total = record.opt_payment.prix * record.nbr_jour_reservation

    opt_klm = fields.Many2one('options', string='Klm illimité')
    opt_klm_name = fields.Char(string='opt_klm name', related='opt_klm.name', store=True)
    opt_klm_price = fields.Integer(string='opt_klm prix', related='opt_klm.prix', store=True)
    opt_kilometrage = fields.Integer(string='Kilometrage', compute='opt_klm_compute', store=True)
    opt_klm_total = fields.Integer(string='Klm illimité', compute='opt_klm_compute', store=True)

    @api.depends('opt_klm')
    def opt_klm_compute(self):
        for record in self:
            if record.opt_klm.type_tarif == 'fixe':
                record.opt_klm_total = record.opt_klm.prix
            else:
                record.opt_klm_total = record.opt_klm.prix * record.nbr_jour_reservation

            if record.opt_klm:
                record.opt_kilometrage = record.opt_klm.limit_Klm * record.nbr_jour_reservation

    opt_protection = fields.Many2one('options', string='protection')
    opt_protection_name = fields.Char(string='opt_protection name', related='opt_protection.name', store=True)
    opt_protection_price = fields.Integer(string='opt_protection prix', related='opt_protection.prix', store=True)
    opt_protection_caution = fields.Integer(string='Caution', related='opt_protection.caution', store=True)
    opt_protection_total = fields.Integer(string='Protection ', compute='opt_protection_compute', store=True)

    @api.depends('total_reduit')
    def _compute_total_badge(self):
        for rec in self:
            # Ajout du symbole Euro
            rec.total_badge = f"{rec.total_reduit} €"

    total_badge = fields.Char(string="Total Badge", compute="_compute_total_badge", store=False)

    @api.depends('opt_protection')
    def opt_protection_compute(self):
        for record in self:
            if record.opt_protection.type_tarif == 'fixe':
                record.opt_protection_total = record.opt_protection.prix
            else:
                record.opt_protection_total = record.opt_protection.prix * record.nbr_jour_reservation

    opt_nd_driver = fields.Many2one('options', string='nd driver')
    opt_nd_driver_name = fields.Char(string='opt_nd_driver name', related='opt_nd_driver.name', store=True)
    opt_nd_driver_price = fields.Integer(string='opt_nd_driver prix', related='opt_nd_driver.prix', store=True)
    opt_nd_driver_total = fields.Integer(string='2ème conducteur', compute='opt_nd_driver_compute', store=True)

    @api.depends('opt_nd_driver')
    def opt_nd_driver_compute(self):
        for record in self:
            if record.opt_nd_driver.type_tarif == 'fixe':
                record.opt_nd_driver_total = record.opt_nd_driver.prix
            else:
                record.opt_nd_driver_total = record.opt_nd_driver.prix * record.nbr_jour_reservation

    opt_plein_carburant = fields.Many2one('options', string='Plein carburant ')
    opt_plein_carburant_name = fields.Char(string='opt_plein_carburant name', related='opt_plein_carburant.name',
                                           store=True)
    opt_plein_carburant_prix = fields.Integer(string='opt_plein_carburant prix', related='opt_plein_carburant.prix',
                                              store=True)
    opt_plein_carburant_total = fields.Integer(string='Plein carburant', compute='opt_plein_carburant_compute',
                                               store=True)

    @api.depends('opt_plein_carburant')
    def opt_plein_carburant_compute(self):
        for record in self:
            if record.opt_plein_carburant.type_tarif == 'fixe':
                record.opt_plein_carburant_total = record.opt_plein_carburant.prix
            else:
                record.opt_plein_carburant_total = record.opt_plein_carburant.prix * record.nbr_jour_reservation

    opt_siege_a = fields.Many2one('options', string='siege a')
    opt_siege_a_name = fields.Char(string='opt_siege_a name', related='opt_siege_a.name', store=True)
    opt_siege_a_prix = fields.Integer(string='opt_siege_a prix', related='opt_siege_a.prix', store=True)
    opt_siege_a_total = fields.Integer(string='Siège Bébé (0-5)Kg', compute='opt_siege_a_compute', store=True)

    @api.depends('opt_siege_a')
    def opt_siege_a_compute(self):
        for record in self:
            if record.opt_siege_a.type_tarif == 'fixe':
                record.opt_siege_a_total = record.opt_siege_a.prix
            else:
                record.opt_siege_a_total = record.opt_siege_a.prix * record.nbr_jour_reservation

    opt_siege_b = fields.Many2one('options', string='siege b')
    opt_siege_b_name = fields.Char(string='opt_siege_b name', related='opt_siege_b.name', store=True)
    opt_siege_b_prix = fields.Integer(string='opt_siege_b prix', related='opt_siege_b.prix', store=True)
    opt_siege_b_total = fields.Integer(string='Siège BéBé (6-13)Kg', compute='opt_siege_b_compute', store=True)

    @api.depends('opt_siege_b')
    def opt_siege_b_compute(self):
        for record in self:
            if record.opt_siege_b.type_tarif == 'fixe':
                record.opt_siege_b_total = record.opt_siege_b.prix
            else:
                record.opt_siege_b_total = record.opt_siege_b.prix * record.nbr_jour_reservation

    opt_siege_c = fields.Many2one('options', string='siege c')
    opt_siege_c_name = fields.Char(string='opt_siege_c name', related='opt_siege_c.name', store=True)
    opt_siege_c_prix = fields.Integer(string='opt_siege_c prix', related='opt_siege_c.prix', store=True)
    opt_siege_c_total = fields.Integer(string='Siège BéBé (13-18)Kg', compute='opt_siege_c_compute', store=True)

    @api.depends('opt_siege_c')
    def opt_siege_c_compute(self):
        for record in self:
            if record.opt_siege_c.type_tarif == 'fixe':
                record.opt_siege_c_total = record.opt_siege_c.prix
            else:
                record.opt_siege_c_total = record.opt_siege_c.prix * record.nbr_jour_reservation

    def send_email_annulation(self):
        template_id = self.env.ref('reservation.template_annulatio_n___').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def reservation_non_abouti(self):
        template_id = self.env.ref('reservation.template_abouti_____').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def prolonga(self):
        template_id = self.env.ref('reservation.template_prolongationnn____').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_otp(self):
        template_id = self.env.ref('reservation.template_ot').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_google(self):
        template_id = self.env.ref('reservation.template_google_').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_retour(self):
        template_id = self.env.ref('reservation.template___retour___').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def action_send_email_retour_avance(self):
        template_id = self.env.ref('reservation.email_retour_avance_template').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def action_send_email_annulation(self):
        template_id = self.env.ref('reservation.email_annulation_template').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def action_send_email_comming_soon(self):
        template_id = self.env.ref('reservation.email_coming_soon_template').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")
    def action_send_confirmation_email(self):
        try:
            template = self.env.ref('reservation.email_confirmation_template')
            for record in self:
                if not record.email:
                    raise UserError(f"Email manquant pour {record.name}")
                # Envoyer l'email et désactiver la suppression auto
                mail_id = template.send_mail(record.id, force_send=True)
                if mail_id:
                    mail = self.env['mail.mail'].browse(mail_id)
                    mail.write({'auto_delete': False})
                    _logger.info(f"Email envoyé et conservé (ID: {mail.id})")
        except Exception as e:
            _logger.error(f"Erreur d'envoi: {str(e)}")
            raise

    @api.depends('livraison', 'livraison.photo')
    def _compute_photo_depart(self):
        for record in self:
            livraison_avant = record.livraison.filtered(lambda l: l.lv_type == 'livraison')
            record.photo_depart = livraison_avant.mapped('photo')

    @api.depends('livraison', 'livraison.kilomtrage', 'nbr_jour_reservation')
    def _compute_klm_moyen(self):
        for record in self:
            if len(record.livraison) >= 2 and record.nbr_jour_reservation > 0:
                first_livraison = record.livraison[0]
                second_livraison = record.livraison[1]

                klm_diff = second_livraison.kilomtrage - first_livraison.kilomtrage
                klm_moyen_value = klm_diff / record.nbr_jour_reservation
                record.klm_moyen_int = klm_moyen_value
                record.klm_moyen = f"{klm_moyen_value:.0f} KM par jour"
            else:
                record.klm_moyen = ""

    @api.depends('etat_reservation')
    def _compute_color(self):
        for record in self:
            if record.etat_reservation == 'reserve':
                record.color = '#FF0000'  # Vert
            elif record.etat_reservation == 'loue':
                record.color = '#00FF00'  # Rouge
            else:
                record.color = '#FFFFFF'

    def create_retour_avance(self):
        return {
            'name': 'Retour a l Avance',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'retour.avance',
            'view_type': 'form',
            'view_id': self.env.ref('reservation.view_retour_avance_pop_up_form').id,
            'target': 'new',
            'context': {
                'default_reservation': self.id,
                'default_date_retour_avance': self.date_heure_fin,
            },
        }

    
    @api.depends('lieu_depart', 'lieu_retour')
    def _compute_depart_retour(self):
        for record in self:
            if record.lieu_depart and record.lieu_retour:
                record.depart_retour = f"{record.lieu_depart.name} ➝ {record.lieu_retour.name}"
            else:
                record.depart_retour = ''

    @api.depends('prolongation.total_prolongation')
    def _compute_total_prolone(self):
        for reservation in self:
            total = sum(prolongation.total_prolongation for prolongation in reservation.prolongation)
            reservation.total_prolone = total

    def action_open_prolongation_popup(self):
        return {
            'name': 'Prolongation',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'prolongation',
            'view_id': self.env.ref('reservation.view_prolongation_popup_form').id,
            'target': 'current',
            'context': {
                'default_reservation': self.id,
            },
        }

    # Méthode pour créer effectivement la prolongation
    @api.model
    def action_create_prolongation(self, vals):
        prolongation = self.env['prolongation'].create(vals)
        if prolongation:
            # Ajoutez ici d'autres actions ou traitements après la création de prolongation
            return {'type': 'ir.actions.act_window_close'}
        return {}

    @api.depends('livraison')
    def _compute_livrer_par(self):
        for record in self:
            livraison_livre = record.livraison.filtered(lambda l: l.lv_type == 'livraison')
            record.livrer_par = livraison_livre[0].livrer_par if livraison_livre else False

    def action_open_cancel_popup(self):
        return {
            'name': 'Annuler Réservation',
            'type': 'ir.actions.act_window',
            'res_model': 'reservation',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('reservation.view_annulation_pop_up_form').id,
            'target': 'new',

        }

    def action_confirm_cancel(self):
        self.status = 'annule'

    def action_open_reject_popup(self):
        return {
            'name': 'Annuler Réservation',
            'type': 'ir.actions.act_window',
            'res_model': 'reservation',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('reservation.view_rejet_pop_up_form').id,
            'target': 'new',
        }

    def action_confirm_reject(self):
        self.status = 'rejete'

    def action_confirm_reservation(self):
        self.ensure_one()
        self.status = 'confirmee'

        livraison_vals = [
            {
                'name': self.name + ' - Livraison',
                'reservation': self.id,
                'lv_type': 'livraison',
            },

            {
                'name': self.name + ' - Réstitution',
                'reservation': self.id,
                'lv_type': 'restitution',
            }
        ]

        for vals in livraison_vals:
            self.env['livraison'].create(vals)

    @api.model
    def create(self, vals):
        if 'date_heure_debut' in vals:
            date_heure_debut = fields.Datetime.from_string(vals['date_heure_debut'])
            # if date_heure_debut < fields.Datetime.now():
            #     raise ValidationError("La date de début ne peut pas être antérieure à la date et l'heure actuelles.")

        record = super(Reservation, self).create(vals)
        if record.status == 'confirmee':
            livraison_vals_1 = {
                'name': record.name,
                'reservation': record.id,
                'lv_type': 'livraison',

            }

            livraison_vals_2 = {
                'name': record.name,
                'reservation': record.id,
                'lv_type': 'restitution',

            }
            self.env['livraison'].create(livraison_vals_1)
            self.env['livraison'].create(livraison_vals_2)

        if record.nd_conducteur == 'oui' and not record.liste_client_id:
            liste_client_model = self.env['liste.client']
            vals = {
                'civilite': record.civilite_nd_condicteur,
                'nom': record.nom_nd_condicteur,
                'prenom': record.prenom_nd_condicteur,
                'email': record.email_nd_condicteur,
                'date_de_naissance': record.date_nd_condicteur,
                'date_de_permis': record.date_de_permis
            }
            liste_client_model.create(vals)

        if record.solde > 0:
            solde = record.solde
            record.solde_reduit = solde
            record.client.solde_consomer += solde
            record.client.solde = 0
            self.env['historique.solde'].create({
                'client': record.client.id,
                'reservation': record.id,
                'montant': solde,
            })

        return record

    def write(self, vals):
        result = super(Reservation, self).write(vals)
        if 'nd_conducteur' in vals and vals['nd_conducteur'] == 'oui':
            for reservation in self.filtered(lambda r: r.nd_conducteur == 'oui' and not r.liste_client_id):
                liste_client_model = self.env['liste.client']
                vals = {
                    'civilite': reservation.civilite_nd_condicteur,
                    'nom': reservation.nom_nd_condicteur,
                    'prenom': reservation.prenom_nd_condicteur,
                    'email': reservation.email_nd_condicteur,
                    'date_de_naissance': reservation.date_nd_condicteur,
                    'date_de_permis': reservation.date_de_permis
                    # Add other fields as needed
                }
                liste_client = liste_client_model.create(vals)
                reservation.liste_client_id = liste_client.id

        return result

    @api.depends('nd_conducteur')
    def _onchange_nd_conducteur(self):
        if self.nd_conducteur == 'oui' and (10 not in self.options.ids):
            self.options = [(4, 10)]
        elif self.nd_conducteur == 'non' and (10 in self.options.ids):
            self.options = [(3, 10)]

    @api.depends('options')
    def _compute_is_nd_cond(self):
        for record in self:
            record.is_nd_cond = any(option.id == 10 for option in record.options)

    @api.constrains('options')
    def _check_options(self):
        for record in self:
            if any(option.id == 10 for option in record.options):
                record.is_nd_cond = True
            else:
                record.is_nd_cond = False

    def _convert_to_float(self, heure_datetime):
        """Convert datetime to float (hours + minutes/60)."""
        return heure_datetime.hour + heure_datetime.minute / 60

    @api.depends('nbr_jour_reservation')
    def _compute_duree_dereservation(self):
        for record in self:
            record.duree_dereservation = f"{record.nbr_jour_reservation} jours"

    @api.model
    def _generate_unique_code_(self):
        current_date = datetime.now()
        year = current_date.strftime('%y')  # Deux derniers chiffres de l'année
        unique_code = ''
        while True:
            random_digits = ''.join(random.choices(string.digits, k=4))  # Quatre chiffres aléatoires
            unique_code = f'{year}{random_digits}'
            if not self.env['reservation'].search([('name', '=', unique_code)]):
                break
        return unique_code

    @api.constrains('vehicule', 'zone')
    def _check_vehicule_zone(self):
        for record in self:
            if record.vehicule.zone != record.zone and not record.zone:
                raise ValidationError(
                    "Le véhicule sélectionné doit appartenir à la même zone que la zone de livraison.")

    @staticmethod
    def _check_date_in_intervals(date_debut, date_fin, intervals):
        for interval in intervals:
            if interval[0] and interval[1]:
                if interval[0] <= date_debut <= interval[1] and interval[0] <= date_fin <= interval[1]:
                    return True
        return False

    @staticmethod
    def _check_date_in_intervals_start(date_debut, date_fin, intervals):
        for interval in intervals:
            if interval[0] and interval[1]:
                if interval[0] <= date_debut <= interval[1] and not (interval[0] <= date_fin <= interval[1]):
                    return True
        return False

    @staticmethod
    def _check_date_in_intervals_end(date_debut, date_fin, intervals):
        for interval in intervals:
            if interval[0] and interval[1]:
                if not (interval[0] <= date_debut <= interval[1]) and interval[0] <= date_fin <= interval[1]:
                    return True
        return False 

    @staticmethod
    def _check_nbr_jour_in_range(nbr_jour, nbr_de, nbr_au):
        return nbr_de <= nbr_jour <= nbr_au

    @api.constrains('nbr_jour_reservation')
    def _check_nbr_jour_reservation(self):
        for record in self:
            if record.nbr_jour_reservation < 3:
                raise ValidationError("Le nombre de jours de réservation ne peut pas être inférieur à 3.")

    @api.model
    def optimize_all_reservations(self):
        print("===== DÉBUT optimize_all_reservations =====")
        all_models = self.env['modele'].search([])
        print(f"Nombre de modèles trouvés: {len(all_models)}")
        for model in all_models:
            print(f"Optimisation du modèle: {model.name}")
            model.optimize_reservations()
            print("Optimisation Ouest")
        print("===== FIN optimize_all_reservations =====")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Optimisation',
                'message': 'Optimisation réussie pour la zone OUEST !',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def optimize_all_reservations_centre(self):
        all_models = self.env['modele'].search([])
        for model in all_models:
            model.optimize_reservations_centre()
            print("Optimisation centre")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Optimisation',
                    'message': 'Optimisation réussie pour la zone CENTRE !',
                    'type': 'success',
                    'sticky': False,
                }
            }

    @api.model
    def optimize_all_reservations_est(self):
        all_models = self.env['modele'].search([])
        for model in all_models:
            model.optimize_reservations_est()
            print("Optimisation est")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Optimisation',
                    'message': 'Optimisation réussie pour la zone EST !',
                    'type': 'success',
                    'sticky': False,
                }
            }


class VehiculeInherit(models.Model):
    _inherit = 'vehicule'

    reservations = fields.One2many('reservation', 'vehicule', string='Reservation')


class ClientInherit(models.Model):
    _inherit = 'liste.client'

    reservations = fields.One2many('reservation', 'client', string='Reservation')
    total_reservation = fields.Monetary(string='Total Réservations', currency_field='devise',
                                        compute='_compute_total_reservation', store=True)
    devise = fields.Many2one()
    duree_concat = fields.Char(string='Durée des Réservations', compute='_compute_duree_concat', store=True)
    total_jour_reservation = fields.Integer(string='Total jrs reservation',
                                            compute='_compute_total_jour_reservation', store=True)
    total_duree_dereservation = fields.Char(string='Total Durée', compute='_compute_total_duree_dereservation',
                                            store=True)
    klm_moyen = fields.Char(string='Kilometrage moyen', compute='_compute_klm_moyen', store=True)
    
    def _cron_recompute_client_fields(self):
        """Recalcule uniquement les clients avec réservations récemment modifiées"""
        _logger.info("=== Début du recalcul des champs clients ===")
        batch_size = 1000
        Client = self.env['liste.client']

        clients_to_recompute = Client.search([
            ('total_reservation', '=', 0),
            ('reservations', '!=', False),
            ('reservations.status', '=', 'confirmee') 
       ])

        if not clients_to_recompute:
            _logger.info("Aucun client à recalculer")
            return True

        total_clients = len(clients_to_recompute)
        _logger.info(f"Total clients à traiter: {total_clients}")

        # Traiter par batch
        for i in range(0, total_clients, batch_size):
            batch_clients = clients_to_recompute[i:i + batch_size]

            try:
                batch_clients._compute_klm_moyen()
                batch_clients._compute_total_reservation()
                batch_clients._compute_total_jour_reservation()
                batch_clients._compute_total_duree_dereservation()
                batch_clients._compute_duree_concat()
                self.env.cr.commit()
                _logger.info(f"✓ Traité {min(i + batch_size, total_clients)}/{total_clients} clients")
            except Exception as e:
                _logger.error(f"✗ Erreur lors du traitement du batch {i // batch_size + 1}: {str(e)}")
                self.env.cr.rollback()

        _logger.info("=== Fin du recalcul ===")
        return True

    def send_email_mise_ajour(self):
        template_id = self.env.ref('reservation.template_mise_').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_activer_compte(self):
        template_id = self.env.ref('reservation.template_activeeeee').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_card_essentiel(self):
        template_id = self.env.ref('reservation.template_essenti').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_mise_ajour_sans(self):
        template_id = self.env.ref('reservation.template_mise_sans__').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_prime_diver(self):
        template_id = self.env.ref('reservation.template_yyyyyyy').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_prime_essentiel(self):
        template_id = self.env.ref('reservation.template___essentiel_essentiel____iss').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_prime_exellent_t(self):
        template_id = self.env.ref('reservation.template_exellent_exellent_exxx_').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_prime_vip(self):
        template_id = self.env.ref('reservation.template_vip_vip_vip_').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_parrainag(self):
        template_id = self.env.ref('reservation.template_parrainage__').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_parrainag_sans(self):
        template_id = self.env.ref('reservation.template_parrainage_san').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_newsletter(self):
        template_id = self.env.ref('reservation.template_newsletteeee').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_card_essentiel(self):
        template_id = self.env.ref('reservation.template_essenti').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_card_essentiel_sans(self):
        template_id = self.env.ref('reservation.template_esse_sans_').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_card_exellent(self):
        template_id = self.env.ref('reservation.template_exellent_exellent_').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_card_exellent_sans(self):
        template_id = self.env.ref('reservation.template_exelle_sans_sans_s').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_card_vip_sans(self):
        template_id = self.env.ref('reservation.template_vippp').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def send_email_card_vip(self):
        template_id = self.env.ref('reservation.template_vip_s').id

        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)

            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    @api.depends('reservations', 'reservations.klm_moyen', 'reservations.klm_moyen_int')
    def _compute_klm_moyen(self):
        for record in self:
            filtered_reservations = record.reservations.filtered(
                lambda r: r.etat_reservation == 'loue' and r.status == 'confirmee')

            klm_values = filtered_reservations.mapped('klm_moyen_int')

            if klm_values:
                klm_average = sum(klm_values) / len(klm_values)
                record.klm_moyen = f"{klm_average:.0f} KM par jour"
            else:
                record.klm_moyen = "0 KM par jour"

    @api.depends('reservations.total_reduit_euro')
    def _compute_total_reservation(self):
        for record in self:
            filtered_reservations = record.reservations.filtered(
                lambda r: r.etat_reservation == 'loue' and r.status == 'confirmee'
            )
            total = sum(reservation.total_reduit_euro for reservation in filtered_reservations)
            record.total_reservation = total

    @api.depends('reservations.nbr_jour_reservation')
    def _compute_total_jour_reservation(self):
        for record in self:
            filtered_reservations = record.reservations.filtered(
                lambda r: r.etat_reservation == 'loue' and r.status == 'confirmee')

            total_jour = sum(reservation.nbr_jour_reservation for reservation in filtered_reservations)
            record.total_jour_reservation = total_jour

    @api.depends('total_jour_reservation')
    def _compute_total_duree_dereservation(self):
        for record in self:
            record.total_duree_dereservation = f"{record.total_jour_reservation} jours"

    @api.depends('reservations.duree_dereservation')
    def _compute_duree_concat(self):
        for record in self:
            filtered_reservations = record.reservations.filtered(
                lambda r: r.etat_reservation == 'loue' and r.status == 'confirmee')

            durees = [reservation.duree_dereservation for reservation in filtered_reservations]
            record.duree_concat = ' , '.join(durees)


class ModelesInherit(models.Model):
    _inherit = 'modele'

    def _optimize_reservations(self):
        """Appelée par le cron"""
        models_to_process = self.search([])
        for model in models_to_process:
            today = datetime.now()

            # Filtrer les véhicules ayant `zone` égal à 1
            filtered_vehicules = model.vehicule_ids.filtered(lambda v: v.zone.id == 1)
            if not filtered_vehicules:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Optimisation',
                        'message': 'Aucun véhicule disponible dans la zone OUEST.',
                        'type': 'warning',
                        'sticky': False,
                    }
                }

            # 1. Rechercher toutes les réservations à partir de la date d'aujourd'hui.
            all_reservations = self.env['reservation'].search(
                [('vehicule.modele', '=', model.id), ('date_heure_debut', '>=', today)],
                order='date_heure_debut'
            )

            if not all_reservations:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Optimisation',
                        'message': 'Rien à optimiser dans la zone OUEST!',
                        'type': 'warning',
                        'sticky': False,
                    }
                }

            # 2. Vider le champ vehicule de toutes les réservations trouvées.
            all_reservations.write({'vehicule': False})

            # 3. Ordonner les réservations par date_heure_debut (croissant).
            reservations_by_start = all_reservations.sorted(key=lambda r: r.date_heure_debut)

            # 4. Ordonner les réservations par date_heure_fin (croissant).
            reservations_by_end = all_reservations.sorted(key=lambda r: r.date_heure_fin)

            # 5. Attribuer les véhicules aux réservations.
            assigned_vehicles = {vehicule.id: datetime.min for vehicule in filtered_vehicules}

            def find_best_vehicle(reservation, assigned_vehicles):
                min_gap = timedelta.max
                best_vehicule = None
                for vehicule_id, last_end_time in assigned_vehicles.items():
                    if last_end_time <= reservation.date_heure_debut:
                        gap = reservation.date_heure_debut - last_end_time
                        if gap < min_gap:
                            min_gap = gap
                            best_vehicule = vehicule_id
                return best_vehicule

            for reservation in reservations_by_start:
                best_vehicule = find_best_vehicle(reservation, assigned_vehicles)
                if best_vehicule:
                    reservation.write({'vehicule': best_vehicule})
                    assigned_vehicles[best_vehicule] = reservation.date_heure_fin
                else:
                    raise ValidationError(
                        f"Pas de véhicule disponible pour la réservation du {reservation.date_heure_debut} au {reservation.date_heure_fin}."
                    )

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Optimisation',
                    'message': 'Optimisation réussie pour la zone OUEST !',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def optimize_reservations_centre(self):
        for model in self:
            today = datetime.now()

            # Filtrer les véhicules ayant `zone` égal à 1
            filtered_vehicules = model.vehicule_ids.filtered(lambda v: v.zone.id == 2)
            if not filtered_vehicules:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Optimisation',
                        'message': 'Aucun véhicule disponible dans la zone CENTRE.',
                        'type': 'warning',
                        'sticky': False,
                    }
                }

            # 1. Rechercher toutes les réservations à partir de la date d'aujourd'hui.
            all_reservations = self.env['reservation'].search(
                [('vehicule.modele', '=', model.id), ('date_heure_debut', '>=', today)],
                order='date_heure_debut'
            )

            if not all_reservations:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Optimisation',
                        'message': 'Rien à optimiser dans la zone CENTRE!',
                        'type': 'warning',
                        'sticky': False,
                    }
                }

            # 2. Vider le champ vehicule de toutes les réservations trouvées.
            all_reservations.write({'vehicule': False})

            # 3. Ordonner les réservations par date_heure_debut (croissant).
            reservations_by_start = all_reservations.sorted(key=lambda r: r.date_heure_debut)

            # 4. Ordonner les réservations par date_heure_fin (croissant).
            reservations_by_end = all_reservations.sorted(key=lambda r: r.date_heure_fin)

            # 5. Attribuer les véhicules aux réservations.
            assigned_vehicles = {vehicule.id: datetime.min for vehicule in filtered_vehicules}

            def find_best_vehicle(reservation, assigned_vehicles):
                min_gap = timedelta.max
                best_vehicule = None
                for vehicule_id, last_end_time in assigned_vehicles.items():
                    if last_end_time <= reservation.date_heure_debut:
                        gap = reservation.date_heure_debut - last_end_time
                        if gap < min_gap:
                            min_gap = gap
                            best_vehicule = vehicule_id
                return best_vehicule

            for reservation in reservations_by_start:
                best_vehicule = find_best_vehicle(reservation, assigned_vehicles)
                if best_vehicule:
                    reservation.write({'vehicule': best_vehicule})
                    assigned_vehicles[best_vehicule] = reservation.date_heure_fin
                else:
                    raise ValidationError(
                        f"Pas de véhicule disponible pour la réservation du {reservation.date_heure_debut} au {reservation.date_heure_fin}."
                    )

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Optimisation',
                    'message': 'Optimisation réussie pour la zone CENTRE !',
                    'type': 'success',
                    'sticky': False,
                }
            }

    def optimize_reservations_est(self):
        for model in self:
            today = datetime.now()

            # Filtrer les véhicules ayant `zone` égal à 1
            filtered_vehicules = model.vehicule_ids.filtered(lambda v: v.zone.id == 3)
            if not filtered_vehicules:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Optimisation',
                        'message': 'Aucun véhicule disponible dans la zone EST.',
                        'type': 'warning',
                        'sticky': False,
                    }
                }

            # 1. Rechercher toutes les réservations à partir de la date d'aujourd'hui.
            all_reservations = self.env['reservation'].search(
                [('vehicule.modele', '=', model.id), ('date_heure_debut', '>=', today)],
                order='date_heure_debut'
            )

            if not all_reservations:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Optimisation',
                        'message': 'Rien à optimiser dans la zone EST!',
                        'type': 'warning',
                        'sticky': False,
                    }
                }

            # 2. Vider le champ vehicule de toutes les réservations trouvées.
            all_reservations.write({'vehicule': False})

            # 3. Ordonner les réservations par date_heure_debut (croissant).
            reservations_by_start = all_reservations.sorted(key=lambda r: r.date_heure_debut)

            # 4. Ordonner les réservations par date_heure_fin (croissant).
            reservations_by_end = all_reservations.sorted(key=lambda r: r.date_heure_fin)

            # 5. Attribuer les véhicules aux réservations.
            assigned_vehicles = {vehicule.id: datetime.min for vehicule in filtered_vehicules}

            def find_best_vehicle(reservation, assigned_vehicles):
                min_gap = timedelta.max
                best_vehicule = None
                for vehicule_id, last_end_time in assigned_vehicles.items():
                    if last_end_time <= reservation.date_heure_debut:
                        gap = reservation.date_heure_debut - last_end_time
                        if gap < min_gap:
                            min_gap = gap
                            best_vehicule = vehicule_id
                return best_vehicule

            for reservation in reservations_by_start:
                best_vehicule = find_best_vehicle(reservation, assigned_vehicles)
                if best_vehicule:
                    reservation.write({'vehicule': best_vehicule})
                    assigned_vehicles[best_vehicule] = reservation.date_heure_fin
                else:
                    raise ValidationError(
                        f"Pas de véhicule disponible pour la réservation du {reservation.date_heure_debut} au {reservation.date_heure_fin}."
                    )

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Optimisation',
                    'message': 'Optimisation réussie pour la zone EST!',
                    'type': 'success',
                    'sticky': False,
                }
            }

    
    @api.model
    def optimize_reservations(self, zone_id=None):
        """
        Si zone_id fourni -> traite seulement cette zone.
        Sinon -> traite toutes les zones trouvées via les vehicules.
        Ne modifie que les réservations dont date_heure_debut >= demain (selon server time).

        NOUVEAU: Ajoute un buffer entre les réservations selon la zone:
        - Zones 1, 2, 16: buffer de 1 heure
        - Autres zones: buffer de 4 heures
        Le buffer est ajouté PHYSIQUEMENT aux dates des réservations (début et fin).

        NOUVEAU: Vérifie les blocages de véhicules (block.car) avant assignation.
        """
        # Temps de référence (Odoo)
        now_str = fields.Datetime.now()
        now_dt = fields.Datetime.from_string(now_str)
        tomorrow_dt = now_dt + relativedelta(days=1)
        tomorrow_str = fields.Datetime.to_string(tomorrow_dt)

        report = []

        # Si zone_id passé -> limiter à cette zone, sinon récupérer toutes les zones liées aux véhicules
        if zone_id:
            # essayer de récupérer l'enregistrement zone s'il existe
            zones = self.env['vehicule'].search([('zone', '!=', False)]).mapped('zone').filtered(
                lambda z: z.id == int(zone_id))
            if not zones:
                _logger.warning("optimize_reservations: zone_id %s introuvable.", zone_id)
        else:
            zones = self.env['vehicule'].search([('zone', '!=', False)]).mapped('zone')
            # si aucune zone trouvée, rien à faire
            if not zones:
                _logger.info("optimize_reservations: aucune zone trouvée via vehicules.")
                return True

        # Parcourir chaque zone
        for zone in zones:
            _logger.info("Optimization: traitement de la zone %s (id=%s)", getattr(zone, 'display_name', zone.id),
                         zone.id)

            # NOUVEAU: Déterminer le buffer selon la zone
            if zone.id in [1, 2, 16]:
                buffer = timedelta(hours=1)
                _logger.info("Zone %s: buffer de 1 heure appliqué", zone.id)
            else:
                buffer = timedelta(hours=4)
                _logger.info("Zone %s: buffer de 4 heures appliqué", zone.id)

            # Pour chaque modele (on peut limiter si tu veux)
            models_to_process = self.search([])

            for modele in models_to_process:
                # 0) véhicules du modèle dans la zone courante
                vehicles = modele.vehicule_ids.filtered(lambda v: v.zone and v.zone.id == zone.id)
                if not vehicles:
                    report.append(f"Zone {zone.id} / {modele.display_name}: aucun véhicule dans cette zone")
                    continue

                # 1) réservations immuables (début < demain) et mobiles (début >= demain) pour ce modèle
                immovable = self.env['reservation'].search([
                    ('modele', '=', modele.id),
                    ('zone', '=', zone.id),
                    ('status', '=', 'confirmee'),
                    ('date_heure_debut', '<', tomorrow_str)
                ])
                movable = self.env['reservation'].search([
                    ('modele', '=', modele.id),
                    ('zone', '=', zone.id),
                    ('status', '=', 'confirmee'),
                    ('date_heure_debut', '>=', tomorrow_str)
                ], order='date_heure_debut')

                if not movable:
                    report.append(
                        f"Zone {zone.id} / {modele.display_name}: rien à optimiser à partir de {tomorrow_str}")
                    continue

                # 2) initialiser assigned: vehicle_id -> last_end (datetime)
                assigned = {}
                epoch = datetime(1970, 1, 1)
                for v in vehicles:
                    assigned[v.id] = epoch

                # Remplir assigned avec réservations immuables qui sont sur des véhicules de cette zone
                for r in immovable:
                    if r.vehicule and r.vehicule.id in assigned:
                        try:
                            r_end = fields.Datetime.from_string(r.date_heure_fin)
                        except Exception:
                            # s'il manque la date_fin, ignorer la réservation
                            _logger.warning("Reservation %s sans date_heure_fin, ignorée pour assigned.", r.id)
                            continue
                        # MODIFIÉ: Ajouter le buffer à la fin de la réservation immuable
                        r_end_with_buffer = r_end + buffer
                        if r_end_with_buffer > assigned[r.vehicule.id]:
                            assigned[r.vehicule.id] = r_end_with_buffer

                # 3) traitement des movable (dans savepoint pour sécurité)
                try:
                    self.env.cr.savepoint()
                    # Optionnel: clear vehicule sur movable avant réassignation
                    movable.write({'vehicule': False})

                    # NOUVEAU: Fonction pour vérifier si un véhicule est bloqué pendant une période
                    def is_vehicle_blocked(vehicle_id, start_datetime, end_datetime):
                        """
                        Vérifie si le véhicule est bloqué pendant la période donnée
                        start_datetime et end_datetime sont des datetime
                        """
                        # Convertir les datetime en date pour comparaison avec block.car
                        start_date = start_datetime.date()
                        end_date = end_datetime.date()

                        # Chercher des blocages qui chevauchent avec la période
                        blocks = self.env['block.car'].search([
                            ('vehicule_id', '=', vehicle_id),
                            ('date_from', '<=', end_date),
                            ('date_to', '>=', start_date)
                        ])

                        if blocks:
                            _logger.info(
                                f"Véhicule {vehicle_id} bloqué du {start_date} au {end_date} - {len(blocks)} blocage(s) trouvé(s)")
                            return True
                        return False

                    def find_best_vehicle(reservation):
                        try:
                            start_dt = fields.Datetime.from_string(reservation.date_heure_debut)
                        except Exception:
                            return None
                        best_vid = None
                        min_gap = timedelta.max
                        for vid, last_end in assigned.items():
                            # Vérifier que le véhicule est disponible (pas occupé)
                            if last_end <= start_dt:
                                # NOUVEAU: Vérifier que le véhicule n'est pas bloqué
                                try:
                                    end_dt = fields.Datetime.from_string(reservation.date_heure_fin)
                                except Exception:
                                    continue

                                if not is_vehicle_blocked(vid, start_dt, end_dt):
                                    gap = start_dt - last_end
                                    if gap < min_gap:
                                        min_gap = gap
                                        best_vid = vid
                                else:
                                    _logger.info(f"Véhicule {vid} ignoré car bloqué pour réservation {reservation.id}")
                        return best_vid

                    assigned_count = 0
                    failed = []
                    blocked_count = 0  # NOUVEAU: Compter les réservations non assignées à cause de blocage
                    modified_reservations = []  # Pour tracker les réservations modifiées

                    for r in movable.sorted(key=lambda x: x.date_heure_debut):
                        # skip si dates manquantes
                        if not r.date_heure_debut or not r.date_heure_fin:
                            _logger.warning("Reservation %s missing dates => skipped", r.id)
                            failed.append(r.id)
                            continue

                        # NOUVEAU: Récupérer les dates originales avant modification
                        original_start = fields.Datetime.from_string(r.date_heure_debut)
                        original_end = fields.Datetime.from_string(r.date_heure_fin)

                        best_vid = find_best_vehicle(r)
                        if best_vid:
                            # NOUVEAU: Ajouter le buffer aux dates réelles de la réservation
                            new_start = original_start + buffer
                            new_end = original_end + buffer

                            # MODIFIÉ: Assigner le véhicule ET modifier les dates avec buffer
                            r.write({
                                'vehicule': best_vid,
                                'date_heure_debut': fields.Datetime.to_string(new_start),
                                'date_heure_fin': fields.Datetime.to_string(new_end)
                            })

                            # NOUVEAU: Tracker les modifications pour les logs
                            modified_reservations.append({
                                'id': r.id,
                                'original_start': original_start,
                                'new_start': new_start,
                                'original_end': original_end,
                                'new_end': new_end
                            })

                            # MODIFIÉ: Mettre à jour assigned avec la nouvelle fin + buffer
                            new_end_with_buffer = new_end + buffer
                            if new_end_with_buffer > assigned[best_vid]:
                                assigned[best_vid] = new_end_with_buffer
                            assigned_count += 1
                        else:
                            failed.append(r.id)
                            # Vérifier si c'est à cause d'un blocage
                            for vid in assigned.keys():
                                if is_vehicle_blocked(vid, original_start, original_end):
                                    blocked_count += 1
                                    break

                    report.append(
                        f"Zone {zone.id} (buffer {buffer}) / {modele.display_name}: assignées {assigned_count}/{len(movable)} ; échouées: {len(failed)} (dont {blocked_count} bloquées)"
                    )
                    if failed:
                        report.append(f" - réservations non assignées ids: {failed}")

                    # NOUVEAU: Log des modifications de dates
                    if modified_reservations:
                        _logger.info("Réservations avec dates modifiées (buffer ajouté):")
                        for mod in modified_reservations:
                            _logger.info(
                                f"  Res {mod['id']}: {mod['original_start']} -> {mod['new_start']} | {mod['original_end']} -> {mod['new_end']}")

                except Exception as e:
                    _logger.exception("Erreur optimisation pour modele %s en zone %s: %s", modele.id, zone.id, e)
                    report.append(f"Zone {zone.id} / {modele.display_name}: erreur durant l'optimisation: {e}")

                    # Logue le rapport global
        _logger.info("Rapport optimisation réservations (multi-zone):\n%s", "\n".join(report))
        return True
