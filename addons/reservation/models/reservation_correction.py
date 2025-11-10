from odoo import fields, models


class ReservationCorrection(models.Model):
    _name = 'reservation.correction'
    _description = 'correction des reservation'
    _rec_name = 'reservation'

    reservation = fields.Many2one('reservation', string='reservation')
    status = fields.Selection([('en_attend', 'En attend'),
                               ('rejete', 'Rejeté'),
                               ('annule', 'Annulé'),
                               ('confirmee', 'Confirmé')], string='Etat confirmation')

    date_depart = fields.Date(string='date depart')
    date_retour = fields.Date(string='date retour')
    heure_depart = fields.Char(string='heure depart')
    heure_retour = fields.Char(string='heure retour')
    vehicule = fields.Many2one('vehicule', string='Véhicule')

    status_new = fields.Selection([('en_attend', 'En attend'),
                               ('rejete', 'Rejeté'),
                               ('annule', 'Annulé'),
                               ('confirmee', 'Confirmé')], string='Etat confirmation')

    date_depart_new = fields.Date(string='date depart')
    date_retour_new = fields.Date(string='date retour')
    heure_depart_new = fields.Char(string='heure depart')
    heure_retour_new = fields.Char(string='heure retour')
    vehicule_new = fields.Many2one('vehicule', string='Véhicule')


