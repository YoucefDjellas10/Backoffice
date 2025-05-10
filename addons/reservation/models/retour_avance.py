from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime


class RetourAvance(models.Model):
    _name = 'retour.avance'
    _description = 'Retoure a lavance'

    name = fields.Char(string='Nom')
    reservation = fields.Many2one('reservation', string='Reservation')
    status = fields.Selection(string='Etat de confirmation', related='reservation.status', store=True)
    etat_reservation = fields.Selection(string='Etat de reservation', related='reservation.etat_reservation',
                                        store=True)
    date_heure_debut = fields.Datetime(string='Date heure debut', related='reservation.date_heure_debut', store=True)
    date_heure_fin = fields.Datetime(string='Date heure fin', related='reservation.date_heure_fin', store=True)
    nbr_jour_reservation = fields.Integer(string='Durée', related='reservation.nbr_jour_reservation', store=True)
    duree_dereservation = fields.Char(string='Durée', related='reservation.duree_dereservation', store=True)

    lieu_depart = fields.Many2one(string='Lieu de départ', related='reservation.lieu_depart', store=True)
    zone = fields.Many2one(string='Zone de depart', related='reservation.zone', store=True)
    lieu_retour = fields.Many2one(string='Lieu de retour', related='reservation.lieu_retour', store=True)
    vehicule = fields.Many2one(string='Véhicule', related='reservation.vehicule', store=True)
    modele = fields.Many2one(string='Modele', related='reservation.modele', store=True)
    categorie = fields.Many2one(string='categorie', related='reservation.categorie', store=True)

    prix_jour = fields.Integer(string='Prix par jours', related='reservation.prix_jour', store=True)
    prix_jour_two = fields.Integer(string='Prix Jour Two', related='reservation.prix_jour_two', store=True)
    nbr_jour_two = fields.Integer(string='Nombre de Jours Two', related='reservation.nbr_jour_two', store=True)
    nbr_jour_one = fields.Integer(string='Nombre de Jours One', related='reservation.nbr_jour_one', store=True)
    frais_de_livraison = fields.Integer(string='Frais de livraison', related='reservation.frais_de_livraison',
                                        store=True)
    options = fields.Many2many(string='Options', related='reservation.options')
    options_total = fields.Integer(string='Total des options', related='reservation.options_total', store=True)
    total = fields.Integer(string='Total Général', related='reservation.total', store=True)
    total_afficher = fields.Integer(string='Total Afficher', related='reservation.total_afficher', store=True)
    prix_jour_afficher = fields.Float(string='Prix par jour Afficher', related='reservation.prix_jour_afficher',
                                      store=True)
    supplements = fields.Integer(string='Supplements', related='reservation.supplements', store=True)
    retour_tard = fields.Integer(string='Retour tard', related='reservation.retour_tard', store=True)

    date_retour_avance = fields.Datetime(string='Date de retour avance', compute='_onchange_date_retour_avance',
                                         store=True, readonly=False)

    differance_heure = fields.Integer(string='Differance Heure')
    Differance_jour = fields.Integer(string='Differance jour')

    def action_save_and_close(self):
        for record in self:
            record.reservation.date_retour_avance = record.date_retour_avance
            record.reservation.retour_avance = True
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('date_heure_fin')
    def _onchange_date_retour_avance(self):
        if self.reservation:
            self.date_retour_avance = self.date_heure_fin

    @api.constrains('date_retour_avance', 'date_heure_fin')
    def _check_date_retour_avance(self):
        for record in self:
            if record.date_retour_avance and record.date_heure_fin and record.date_retour_avance >= record.date_heure_fin:
                raise ValidationError("La date de retour avancé ne peut pas être après la date de fin.")

    @api.depends('date_retour_avance', 'date_heure_fin')
    def _compute_differences(self):
        for record in self:
            if record.date_retour_avance and record.date_heure_fin:
                delta = record.date_heure_fin - record.date_retour_avance
                record.differance_heure = delta.seconds // 3600
                record.Differance_jour = delta.days

    @api.onchange('date_retour_avance', 'date_heure_fin')
    def _onchange_compute_differences(self):
        self._compute_differences()
