from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import random
import string
import logging
import requests
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
        compute="_compute_create_date_trimmed",
        store=False
    )

    def _compute_create_date_trimmed(self):
        for record in self:
            if record.create_date:
                record.create_date_trimmed = record.create_date.strftime('%Y-%m-%d %H:%M')

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

    nbr_jour_reservation = fields.Integer(string='Durée',
                                          compute='_compute_nbr_jour_reservation', store=True)
    duree_dereservation = fields.Char(string='Durée', compute='_compute_duree_dereservation', store=True)

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
    lecart = fields.Integer(string='L\'écart')

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

    prix_jour = fields.Integer(string='Prix par jours', compute='_compute_prix_jour', store=True)
    prix_jour_two = fields.Integer(string='Prix Jour Two')
    nbr_jour_two = fields.Integer(string='Nombre de Jours Two')
    nbr_jour_one = fields.Integer(string='Nombre de Jours One')
    frais_de_livraison = fields.Integer(string='Frais de livraison', compute='_compute_frais_livraison', store=True)
    options = fields.Many2many('options', string='Options', store=True, domain="[('id', '!=', 10)]")
    options_total = fields.Integer(string='Total des options', compute='_compute_options_total', store=True)
    options_total_reduit = fields.Integer(string='Total options reduit', compute='_compute_options_total_reduit',
                                          store=True)

    total = fields.Integer(string='Total Général', compute='_compute_total', store=True)
    total_reduit = fields.Integer(string='Total Réduit', compute='_compute_total_reduit', store=True)

    currency_id_reduit = fields.Many2one('res.currency', string='Currency',
                                         default=lambda self: self.env['res.currency'].browse(125).id)
    total_reduit_euro = fields.Monetary(string='Total Réduit (EUR)', currency_field='currency_id_reduit',
                                        compute='_compute_total_reduit_euro', store=True)
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

            # Retourne une action pour ouvrir le form view en pop-up
            return {
                'type': 'ir.actions.act_window',
                'name': 'Modifier la réservation',
                'res_model': 'edit.reservation',
                'view_mode': 'form',
                'res_id': edit_res.id,
                'target': 'new',  # ouvre en modal
            }
   
    @api.depends('total_revenue')
    def _compute_montant_paye(self):
        for record in self:
            record.montant_paye = record.total_revenue

    @api.depends('lecart', 'montant_paye', 'total_degrader', 'total_ecce_klm', 'total_reduit_euro')
    def _compute_reste_payer(self):
        for r in self:
            rest = (r.total_reduit_euro or 0) + (r.total_degrader or 0) + (r.total_ecce_klm or 0) \
                   - (r.montant_paye or 0) - (r.lecart or 0)
            r.reste_payer = rest if rest > 0 else 0
            _logger.info("compute reste_payer for id %s -> %s", r.id, r.reste_payer)

    @api.onchange('lecart', 'montant_paye', 'total_degrader', 'total_ecce_klm', 'total_reduit_euro')
    def _onchange_reste_payer(self):
        # seulement pour rafraîchir la vue avant sauvegarde
        for r in self:
            rest = (r.total_reduit_euro or 0) + (r.total_degrader or 0) + (r.total_ecce_klm or 0) \
                   - (r.montant_paye or 0) - (r.lecart or 0)
            r.reste_payer = rest if rest > 0 else 0


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

    @api.depends('total_reduit')
    def _compute_total_reduit_euro(self):
        for record in self:
            record.total_reduit_euro = record.total_reduit

    total_afficher = fields.Integer(string='Total Afficher', compute='_compute_total_afficher', store=True)
    total_afficher_reduit = fields.Integer(string='Total Afficher reduit', compute='_compute_total_afficher_reduit',
                                           store=True)
    prix_jour_afficher = fields.Float(string='Prix par jour Afficher',
                                      compute='_compute_prix_jour_afficher', store=True)
    prix_jour_afficher_reduit = fields.Float(string='Prix par jour reduit',
                                             compute='_compute_prix_jour_afficher_reduit', store=True)
    supplements = fields.Integer(string='Supplements', compute='_compute_supplements', store=True)
    retour_tard = fields.Integer(string='Retour tard', compute='_compute_retour_tard', store=True)
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
    frais_de_dossier = fields.Integer(string='Frais de dossier', compute='_compute_frais_de_dossier', store=True)
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

    @api.depends('total_afficher', 'reduction')
    def _compute_total_afficher_reduit(self):
        for record in self:
            reduction_amount = (record.total_afficher * record.reduction) / 100
            record.total_afficher_reduit = record.total_afficher - reduction_amount

    @api.depends('options', 'options_gratuit', 'nbr_jour_reservation')
    def _compute_options_total_reduit(self):
        for reservation in self:
            total_reduit = 0
            if reservation.options_gratuit:
                for option in reservation.options:
                    if option in reservation.options_gratuit:
                        if option.type_tarif == 'fixe':
                            total_reduit += option.prix
                        else:
                            total_reduit += option.prix * reservation.nbr_jour_reservation
            reservation.options_total_reduit = total_reduit

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

    @api.depends('nbr_jour_reservation')
    def _compute_frais_de_dossier(self):
        options_record = self.env['options'].browse(19)
        if options_record:
            self.frais_de_dossier = options_record.prix
        else:
            self.frais_de_dossier = 0

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

    @api.constrains('date_heure_debut', 'date_heure_fin', 'vehicule')
    def _check_vehicle_availability(self):
        for record in self:
            if not record.vehicule:
                continue
            overlapping_reservations = self.env['reservation'].search([
                ('vehicule', '=', record.vehicule.id),
                ('id', '!=', record.id),
                ('date_heure_debut', '<', record.date_heure_fin),
                ('date_heure_fin', '>', record.date_heure_debut),
            ])
            if overlapping_reservations:
                raise ValidationError(
                    f"Le véhicule {record.vehicule.name} n'est pas disponible entre {record.date_heure_debut} et {record.date_heure_fin}."
                )

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

    @api.depends('date_heure_debut', 'date_heure_fin')
    def _compute_retour_tard(self):
        for record in self:
            if record.date_heure_debut and record.date_heure_fin:
                debut_time = record.date_heure_debut.time()
                fin_time = record.date_heure_fin.time()

                debut_total_minutes = debut_time.hour * 60 + debut_time.minute
                fin_total_minutes = fin_time.hour * 60 + fin_time.minute

                ecart_minutes = abs(fin_total_minutes - debut_total_minutes)

                ecart_heures = ecart_minutes / 60

                supplements = self.env['supplements'].search([('valeur', '>', 0)])
                retour_tard_value = 0

                for supplement in supplements:
                    if ecart_heures > supplement.reatrd:
                        if record.prix_jour_two > 0:
                            retour_tard_value = record.prix_jour_two * 2 / 3
                        else:
                            retour_tard_value = record.prix_jour * 2 / 3
                        break

                record.retour_tard = retour_tard_value
            else:
                record.retour_tard = 0

    @api.depends('date_heure_debut', 'date_heure_fin', 'date_retour_avance')
    def _compute_supplements(self):
        for record in self:
            supplements_value = 0
            avance = 0
            heure_retour_avance_float = None

            heure_debut_float = self._convert_to_float(record.date_heure_debut + timedelta(hours=1))
            heure_fin_float = self._convert_to_float(record.date_heure_fin + timedelta(hours=1))
            if record.date_retour_avance :
                heure_retour_avance_float = self._convert_to_float(record.date_retour_avance + timedelta(hours=1))

            supplements = self.env['supplements'].search([])

            for supplement in supplements:
                if supplement.heure_debut_float <= heure_debut_float < supplement.heure_fin_float:
                    supplements_value += supplement.montant

            for supplement in supplements:
                if heure_retour_avance_float is not None and supplement.heure_debut_float <= heure_fin_float < supplement.heure_fin_float:
                    supplements_value += supplement.montant
                    avance = 1

            for supplement in supplements:
                if supplement.heure_debut_float and heure_retour_avance_float and supplement.heure_fin_float:
                    if supplement.heure_debut_float <= heure_retour_avance_float < supplement.heure_fin_float and avance == 0:
                        supplements_value += supplement.montant

            record.supplements = supplements_value

    def _convert_to_float(self, heure_datetime):
        """Convert datetime to float (hours + minutes/60)."""
        return heure_datetime.hour + heure_datetime.minute / 60

    @api.depends('nbr_jour_reservation')
    def _compute_duree_dereservation(self):
        for record in self:
            record.duree_dereservation = f"{record.nbr_jour_reservation} jours"

    @api.depends('prix_jour', 'nbr_jour_one', 'prix_jour_two', 'nbr_jour_two', 'frais_de_livraison',
                 'supplements', 'retour_tard')
    def _compute_total_afficher(self):
        for reservation in self:
            reservation.total_afficher = reservation.prix_jour * reservation.nbr_jour_one + \
                                         reservation.prix_jour_two * reservation.nbr_jour_two + \
                                         reservation.frais_de_livraison + \
                                         reservation.supplements + reservation.retour_tard

    @api.depends('total_afficher', 'nbr_jour_reservation')
    def _compute_prix_jour_afficher(self):
        for reservation in self:
            if reservation.nbr_jour_reservation != 0:
                reservation.prix_jour_afficher = reservation.total_afficher / reservation.nbr_jour_reservation
            else:
                reservation.prix_jour_afficher = 0

    @api.depends('total_afficher_reduit', 'nbr_jour_reservation')
    def _compute_prix_jour_afficher_reduit(self):
        for reservation in self:
            if reservation.nbr_jour_reservation != 0:
                reservation.prix_jour_afficher_reduit = reservation.total_afficher_reduit / reservation.nbr_jour_reservation
            else:
                reservation.prix_jour_afficher = 0

    @api.depends('frais_de_dossier', 'supplements', 'total_afficher', 'options')
    def _compute_total(self):
        for reservation in self:
            total_general = reservation.frais_de_dossier + reservation.options_total + reservation.total_afficher
            reservation.total = total_general

    @api.depends('lecart','options_total', 'total_afficher_reduit', 'frais_de_dossier', 'options_total_reduit', 'solde_reduit')
    def _compute_total_reduit(self):
        for reservation in self:
            total_general = reservation.frais_de_dossier + reservation.total_afficher_reduit + reservation.options_total - reservation.options_total_reduit - reservation.solde_reduit + reservation.lecart
            reservation.total_reduit = total_general

    @api.depends('opt_payment_total', 'opt_klm_total', 'opt_nd_driver_total', 'opt_plein_carburant_total',
                 'opt_siege_a_total', 'opt_siege_b_total', 'opt_siege_c_total', 'opt_protection')
    def _compute_options_total(self):
        for reservation in self:
            reservation.options_total = reservation.opt_payment_total + reservation.opt_klm_total + reservation.opt_nd_driver_total + reservation.opt_plein_carburant_total + reservation.opt_siege_a_total + reservation.opt_siege_b_total + reservation.opt_siege_c_total + reservation.opt_protection_total

    @api.depends('lieu_depart', 'lieu_retour')
    def _compute_frais_livraison(self):
        for reservation in self:
            frais_livraison = self.env['frais.livraison'].search([
                ('depart', '=', reservation.lieu_depart.id),
                ('retour', '=', reservation.lieu_retour.id)
            ], limit=1)
            if frais_livraison:
                reservation.frais_de_livraison = frais_livraison.montant
            else:
                reservation.frais_de_livraison = 0

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

    @api.depends('date_heure_debut', 'date_heure_fin')
    def _compute_nbr_jour_reservation(self):
        for record in self:
            if record.date_heure_debut and record.date_heure_fin:
                date_debut = record.date_heure_debut.date()
                date_fin = record.date_heure_fin.date()

                delta_days = (date_fin - date_debut).days
                record.nbr_jour_reservation = delta_days
            else:
                record.nbr_jour_reservation = 0

    @api.depends('date_heure_debut', 'date_heure_fin', 'nbr_jour_reservation', 'modele')
    def _compute_prix_jour(self):
        for record in self:
            if not record.modele:
                continue

            intervals_t_one_un = [
                (record.modele.date_depart_one_t_one, record.modele.date_fin_one_t_one),
            ]
            intervals_t_one_deux = [
                (record.modele.date_depart_two_t_one, record.modele.date_fin_two_t_one),
            ]
            intervals_t_one_trois = [
                (record.modele.date_depart_three_t_one, record.modele.date_fin_three_t_one),
            ]
            intervals_t_one_quatre = [
                (record.modele.date_depart_four_t_one, record.modele.date_fin_four_t_one),
            ]

            intervals_t_two_un = [
                (record.modele.date_depart_one_t_two, record.modele.date_fin_one_t_two),
            ]
            intervals_t_two_deux = [
                (record.modele.date_depart_two_t_two, record.modele.date_fin_two_t_two),
            ]
            intervals_t_two_trois = [
                (record.modele.date_depart_three_t_two, record.modele.date_fin_three_t_two),
            ]
            intervals_t_two_quatre = [
                (record.modele.date_depart_four_t_two, record.modele.date_fin_four_t_two),
            ]

            intervals_t_three_un = [
                (record.modele.date_depart_one_t_three, record.modele.date_fin_one_t_three),
            ]
            intervals_t_three_deux = [
                (record.modele.date_depart_two_t_three, record.modele.date_fin_two_t_three),
            ]
            intervals_t_three_trois = [
                (record.modele.date_depart_three_t_three, record.modele.date_fin_three_t_three),
            ]
            intervals_t_three_quatre = [
                (record.modele.date_depart_four_t_three, record.modele.date_fin_four_t_three),
            ]

            intervals_t_four_un = [
                (record.modele.date_depart_one_t_four, record.modele.date_fin_one_t_four),
            ]
            intervals_t_four_deux = [
                (record.modele.date_depart_two_t_four, record.modele.date_fin_two_t_four),
            ]
            intervals_t_four_trois = [
                (record.modele.date_depart_three_t_four, record.modele.date_fin_three_t_four),
            ]
            intervals_t_four_quatre = [
                (record.modele.date_depart_four_t_four, record.modele.date_fin_four_t_four),
            ]

            intervals_t_five = [
                (record.modele.date_depart_one_t_five, record.modele.date_fin_one_t_five),
                (record.modele.date_depart_two_t_five, record.modele.date_fin_two_t_five),
                (record.modele.date_depart_three_t_five, record.modele.date_fin_three_t_five),
                (record.modele.date_depart_four_t_five, record.modele.date_fin_four_t_five),
            ]
            intervals_t_six = [
                (record.modele.date_depart_one_t_six, record.modele.date_fin_one_t_six),
                (record.modele.date_depart_two_t_six, record.modele.date_fin_two_t_six),
                (record.modele.date_depart_three_t_six, record.modele.date_fin_three_t_six),
                (record.modele.date_depart_four_t_six, record.modele.date_fin_four_t_six),
            ]
            intervals_t_seven = [
                (record.modele.date_depart_one_t_seven, record.modele.date_fin_one_t_seven),
                (record.modele.date_depart_two_t_seven, record.modele.date_fin_two_t_seven),
                (record.modele.date_depart_three_t_seven, record.modele.date_fin_three_t_seven),
                (record.modele.date_depart_four_t_seven, record.modele.date_fin_four_t_seven),
            ]
            intervals_t_eight = [
                (record.modele.date_depart_one_t_eight, record.modele.date_fin_one_t_eight),
                (record.modele.date_depart_two_t_eight, record.modele.date_fin_two_t_eight),
                (record.modele.date_depart_three_t_eight, record.modele.date_fin_three_t_eight),
                (record.modele.date_depart_four_t_eight, record.modele.date_fin_four_t_eight),
            ]
            intervals_t_nine = [
                (record.modele.date_depart_one_t_nine, record.modele.date_fin_one_t_nine),
                (record.modele.date_depart_two_t_nine, record.modele.date_fin_two_t_nine),
                (record.modele.date_depart_three_t_nine, record.modele.date_fin_three_t_nine),
                (record.modele.date_depart_four_t_nine, record.modele.date_fin_four_t_nine),
            ]
            intervals_t_ten = [
                (record.modele.date_depart_one_t_ten, record.modele.date_fin_one_t_ten),
                (record.modele.date_depart_two_t_ten, record.modele.date_fin_two_t_ten),
                (record.modele.date_depart_three_t_ten, record.modele.date_fin_three_t_ten),
                (record.modele.date_depart_four_t_ten, record.modele.date_fin_four_t_ten),
            ]

            date_heure_debut = record.date_heure_debut.date() if isinstance(record.date_heure_debut,
                                                                            datetime) else record.date_heure_debut
            date_heure_fin = record.date_heure_fin.date() if isinstance(record.date_heure_fin,
                                                                        datetime) else record.date_heure_fin

            if self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_one_un) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                  record.modele.nbr_au_t_one):
                record.prix_jour = record.modele.prix_one
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_one_deux) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                  record.modele.nbr_au_t_one):
                record.prix_jour = record.modele.prix_one
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_one_trois) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                  record.modele.nbr_au_t_one):
                record.prix_jour = record.modele.prix_one
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_one_quatre) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                  record.modele.nbr_au_t_one):
                record.prix_jour = record.modele.prix_one
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0

            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_two_un) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                  record.modele.nbr_au_t_two):
                record.prix_jour = record.modele.prix_two
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_two_deux) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                  record.modele.nbr_au_t_two):
                record.prix_jour = record.modele.prix_two
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_two_trois) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                  record.modele.nbr_au_t_two):
                record.prix_jour = record.modele.prix_two
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_two_quatre) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                  record.modele.nbr_au_t_two):
                record.prix_jour = record.modele.prix_two
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0

            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_three_un) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                  record.modele.nbr_au_t_three):
                record.prix_jour = record.modele.prix_three
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_three_deux) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                  record.modele.nbr_au_t_three):
                record.prix_jour = record.modele.prix_three
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_three_trois) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                  record.modele.nbr_au_t_three):
                record.prix_jour = record.modele.prix_three
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_three_quatre) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                  record.modele.nbr_au_t_three):
                record.prix_jour = record.modele.prix_three
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0

            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_four_un) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                  record.modele.nbr_au_t_four):
                record.prix_jour = record.modele.prix_four
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_four_deux) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                  record.modele.nbr_au_t_four):
                record.prix_jour = record.modele.prix_four
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_four_trois) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                  record.modele.nbr_au_t_four):
                record.prix_jour = record.modele.prix_four
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0
            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_four_quatre) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                  record.modele.nbr_au_t_four):
                record.prix_jour = record.modele.prix_four
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0

            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_five) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                  record.modele.nbr_au_t_five):
                record.prix_jour = record.modele.prix_five
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0

            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_six) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                  record.modele.nbr_au_t_six):
                record.prix_jour = record.modele.prix_six
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0

            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_seven) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                  record.modele.nbr_au_t_seven):
                record.prix_jour = record.modele.prix_seven
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0

            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_eight) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                  record.modele.nbr_au_t_eight):
                record.prix_jour = record.modele.prix_eight
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0

            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_nine) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                  record.modele.nbr_au_t_nine):
                record.prix_jour = record.modele.prix_nine
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0

            elif self._check_date_in_intervals(date_heure_debut, date_heure_fin, intervals_t_ten) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                  record.modele.nbr_au_t_ten):
                record.prix_jour = record.modele.prix_ten
                record.nbr_jour_one = record.nbr_jour_reservation
                record.prix_jour_two = 0
                record.nbr_jour_two = 0

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_one_un) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                  record.modele.nbr_au_t_one):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_one_un if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_one_un) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                      record.modele.nbr_au_t_one):
                    record.prix_jour = record.modele.prix_one
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_one_deux) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                  record.modele.nbr_au_t_one):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_one_deux if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_one_deux) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                      record.modele.nbr_au_t_one):
                    record.prix_jour = record.modele.prix_one
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_one_trois) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                  record.modele.nbr_au_t_one):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_one_trois if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_one_trois) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                      record.modele.nbr_au_t_one):
                    record.prix_jour = record.modele.prix_one
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_one_quatre) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                  record.modele.nbr_au_t_one):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_one_quatre if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_one_quatre) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                      record.modele.nbr_au_t_one):
                    record.prix_jour = record.modele.prix_one
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_two_un) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                  record.modele.nbr_au_t_two):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_two_un if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_two_un) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                      record.modele.nbr_au_t_two):
                    record.prix_jour = record.modele.prix_two
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_two_deux) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                  record.modele.nbr_au_t_two):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_two_deux if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_two_deux) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                      record.modele.nbr_au_t_two):
                    record.prix_jour = record.modele.prix_two
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_two_trois) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                  record.modele.nbr_au_t_two):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_two_trois if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_two_trois) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                      record.modele.nbr_au_t_two):
                    record.prix_jour = record.modele.prix_two
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_two_quatre) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                  record.modele.nbr_au_t_two):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_two_quatre if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_two_quatre) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                      record.modele.nbr_au_t_two):
                    record.prix_jour = record.modele.prix_two
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_three_un) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                  record.modele.nbr_au_t_three):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_three_un if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_three_un) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                      record.modele.nbr_au_t_three):
                    record.prix_jour = record.modele.prix_three
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_three_deux) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                  record.modele.nbr_au_t_three):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_three_deux if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_three_deux) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                      record.modele.nbr_au_t_three):
                    record.prix_jour = record.modele.prix_three
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_three_trois) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                  record.modele.nbr_au_t_three):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_three_trois if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_three_trois) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                      record.modele.nbr_au_t_three):
                    record.prix_jour = record.modele.prix_three
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_three_quatre) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                  record.modele.nbr_au_t_three):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_three_quatre if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_three_quatre) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                      record.modele.nbr_au_t_three):
                    record.prix_jour = record.modele.prix_three
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_four_un) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                  record.modele.nbr_au_t_four):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_four_un if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_four_un) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                      record.modele.nbr_au_t_four):
                    record.prix_jour = record.modele.prix_four
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_four_deux) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                  record.modele.nbr_au_t_four):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_four_deux if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_four_deux) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                      record.modele.nbr_au_t_four):
                    record.prix_jour = record.modele.prix_four
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_four_trois) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                  record.modele.nbr_au_t_four):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_four_trois if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_four_trois) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                      record.modele.nbr_au_t_four):
                    record.prix_jour = record.modele.prix_four
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_four_quatre) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                  record.modele.nbr_au_t_four):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_four_quatre if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_four_quatre) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                      record.modele.nbr_au_t_four):
                    record.prix_jour = record.modele.prix_four
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_five) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                          record.modele.nbr_au_t_five):
                        record.prix_jour_two = record.modele.prix_five
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_six) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                          record.modele.nbr_au_t_six):
                        record.prix_jour_two = record.modele.prix_six
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_seven) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                          record.modele.nbr_au_t_seven):
                        record.prix_jour_two = record.modele.prix_seven
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_eight) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                          record.modele.nbr_au_t_eight):
                        record.prix_jour_two = record.modele.prix_eight
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_nine) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                          record.modele.nbr_au_t_nine):
                        record.prix_jour_two = record.modele.prix_nine
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_ten) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                          record.modele.nbr_au_t_ten):
                        record.prix_jour_two = record.modele.prix_ten
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_five) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                  record.modele.nbr_au_t_five):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_five if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_five) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_five,
                                                      record.modele.nbr_au_t_five):
                    record.prix_jour = record.modele.prix_five
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_six) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                  record.modele.nbr_au_t_six):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_six if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_six) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_six,
                                                      record.modele.nbr_au_t_six):
                    record.prix_jour = record.modele.prix_six
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_seven) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                  record.modele.nbr_au_t_seven):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_seven if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_seven) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_seven,
                                                      record.modele.nbr_au_t_seven):
                    record.prix_jour = record.modele.prix_seven
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_eight) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                  record.modele.nbr_au_t_eight):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_eight if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_eight) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_eight,
                                                      record.modele.nbr_au_t_eight):
                    record.prix_jour = record.modele.prix_eight
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_nine) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                  record.modele.nbr_au_t_nine):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_nine if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_nine) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_nine,
                                                      record.modele.nbr_au_t_nine):
                    record.prix_jour = record.modele.prix_nine
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            elif self._check_date_in_intervals_start(date_heure_debut, date_heure_fin, intervals_t_ten) and \
                    self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                  record.modele.nbr_au_t_ten):
                final_date = max(date_fin for date_depart, date_fin in intervals_t_ten if date_fin)
                final_date_one = final_date + timedelta(days=1)
                if self._check_date_in_intervals(date_heure_debut, final_date, intervals_t_ten) and \
                        self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_ten,
                                                      record.modele.nbr_au_t_ten):
                    record.prix_jour = record.modele.prix_ten
                    date_diff = (final_date - date_heure_debut).days
                    record.nbr_jour_one = date_diff + 1
                    if self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_one_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_one,
                                                          record.modele.nbr_au_t_one):
                        record.prix_jour_two = record.modele.prix_one
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_two_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_two,
                                                          record.modele.nbr_au_t_two):
                        record.prix_jour_two = record.modele.prix_two
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_three_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_three,
                                                          record.modele.nbr_au_t_three):
                        record.prix_jour_two = record.modele.prix_three
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_un) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_deux) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_trois) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one
                    elif self._check_date_in_intervals(final_date_one, date_heure_fin, intervals_t_four_quatre) and \
                            self._check_nbr_jour_in_range(record.nbr_jour_reservation, record.modele.nbr_de_t_four,
                                                          record.modele.nbr_au_t_four):
                        record.prix_jour_two = record.modele.prix_four
                        date_diff_one = (date_heure_fin - final_date_one).days
                        record.nbr_jour_two = date_diff_one

            else:
                record.prix_jour = 0
                record.prix_jour_two = 0
                record.nbr_jour_one = 0
                record.nbr_jour_two = 0

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
        all_models = self.env['modele'].search([])
        for model in all_models:
            model.optimize_reservations()
            print("Optimisation Ouest")
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

    def optimize_reservations(self):
        for model in self:
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
