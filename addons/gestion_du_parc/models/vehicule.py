from odoo import fields, models, api, exceptions
from datetime import datetime, timedelta

class Vehicule(models.Model):
    _name = 'vehicule'
    _description = 'Véhicules par modele et categorie'
    _rec_name = 'numero'

    name = fields.Char(string='Véhicule', compute='_compute_name', store=True)
    matricule = fields.Char(string='Matricule', required=True)
    numero = fields.Char(string='Numéro', required=True)
    couleur = fields.Char(string='Couleur')
    couleur_tag = fields.Integer(string='Couleur', compute='_compute_couleur_tag', store=True)
    modele = fields.Many2one('modele', string='Modele')
    model_name = fields.Char(string='Nom du modèle', related='modele.name', store=True)
    categorie = fields.Many2one(string='categorie', related='modele.categorie', store=True)
    carburant = fields.Selection(string='Carburant', related='modele.carburant', store=True)
    age_min = fields.Char(string='Carburant', related='modele.min_age', store=True)
    sticker = fields.Selection(string='Carburant', related='modele.stickers', store=True)
    nombre_deplace = fields.Char(string='Nombre de places', related='modele.nombre_deplace', store=True)
    nombre_de_porte = fields.Char(string='Nombre de portes', related='modele.nombre_de_porte', store=True)
    nombre_de_bagage = fields.Char(string='Nombre de bagages', related='modele.nombre_de_bagage', store=True)
    climatisation = fields.Selection(string='Climatisée', related='modele.climatisation', store=True)
    boite_vitesse = fields.Selection(string='Boite Vitesse', related='modele.boite_vitesse', store=True)
    stickers = fields.Selection(string='Autocollant', related='modele.stickers', store=True)
    marketing_text_fr = fields.Char(string='Marketing Text (FR)', related='modele.marketing_text_fr', store=True)
    photo_link = fields.Char(string='Lien de la photo', related='modele.photo_link', store=True)
    photo_link_nd = fields.Char(string='Lien de la 2eme photo', related='modele.photo_link_nd', store=True)
    zone = fields.Many2one('zone', string='Zone de livraison', create=False)
    date_debut_service = fields.Date(string='Date mis en service')
    date_fin_service = fields.Date(string='Date fin de service')
    dernier_klm = fields.Integer(string='Dernier kilometrage')
    active_test = fields.Boolean(string='Actif', default=True)
    euro = fields.Many2one('res.currency', string='euro',
                           default=lambda self: self.env['res.currency'].browse(125).id)
    dinar = fields.Many2one('res.currency', string='Dinar algérien',
                            default=lambda self: self.env['res.currency'].browse(111).id)
    prix_achat = fields.Monetary(currency_field='dinar', string='Prix d\'achat', compute='_compute_prix_achat_eur_dzd',
                                 store=True, readonly=False)
    prix_achat_eur = fields.Monetary(currency_field='euro', string='Prix d\'achat',
                                     compute='_compute_prix_achat_eur_dzd', store=True, readonly=False)
    color = fields.Selection([('noir', 'Noir'), ('blanc', 'Blanc'), ('gris', 'Gris'), ('bleu', 'Bleu'),
                              ('rouge', 'Rouge'), ('argent', 'Argent'), ('vert', 'Vert'), ('orange', 'Orange'),
                              ('marron', 'Marron'), ('violet', 'Violet'), ('beige', 'Beige'), ('bronze', 'Bronze'),
                              ('bordeaux', 'Bordeaux')], string='Couleur de véhicule')

    @api.depends('prix_achat_eur', 'prix_achat')
    def _compute_prix_achat_eur_dzd(self):
        for record in self:
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            if taux_change:
                taux = taux_change.montant
                if record.prix_achat:
                    record.prix_achat_eur = record.prix_achat / taux
                elif record.prix_achat_eur:
                    record.prix_achat = record.prix_achat_eur * taux
            else:
                record.prix_achat = 0
                record.prix_achat_eur = 0

    @api.depends('active_test')
    def _compute_couleur_tag(self):
        for record in self:
            if record.active_test:
                record.couleur_tag = 10  # Vert
            else:
                record.couleur_tag = 1  # Rouge

    @api.depends('matricule', 'numero')
    def _compute_name(self):
        for vehicule in self:
            if vehicule.matricule and vehicule.numero:
                vehicule.name = f"{vehicule.matricule} ({vehicule.numero})"
            elif vehicule.matricule:
                vehicule.name = vehicule.matricule
            elif vehicule.numero:
                vehicule.name = vehicule.numero
            else:
                vehicule.name = ""

    @api.model
    def verifier_ou_creer_reservation(self, *args):
        for vehicule in self:
            # Vérifier si une réservation existe déjà pour ce véhicule
            reservation_existante = self.env['reservation'].search([('vehicule', '=', vehicule.id)], limit=1)
            print("1")

            if not reservation_existante:
                if not vehicule.date_debut_service:
                    raise exceptions.UserError(
                        f"Le véhicule {vehicule.name} n'a pas de date de début de service définie."
                    )

                # Définir les dates de début et de fin pour la réservation
                date_debut = datetime.combine(vehicule.date_debut_service, datetime.min.time()) + timedelta(hours=0)
                date_fin = date_debut + timedelta(hours=1)

                # Créer la réservation
                self.env['reservation'].create({
                    'vehicule': vehicule.id,
                    'lieu_depart': vehicule.zone.id,
                    'lieu_retour': vehicule.zone.id,
                    'date_heure_debut': date_debut,
                    'date_heure_fin': date_fin,
                    'client': self.env['liste.client'].search([], limit=1).id,
                })
