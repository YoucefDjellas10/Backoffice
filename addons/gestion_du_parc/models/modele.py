from odoo import fields, models


class Modeles(models.Model):
    _name = 'modele'
    _description = 'modele de vehicule'

    name = fields.Char(string='Nom du modèle')
    min_age = fields.Char(string='Age min')
    show_order_model = fields.Integer(string='Ordre d affichage')
    caution_classic = fields.Float(string='Caution classique', related='categorie.caution_classic', store=True)
    caution_red = fields.Float(string='Caution Réduite', related='categorie.caution_red', store=True)
    carburant = fields.Selection([('essence', 'Essence'),
                                  ('diesel', 'Diesel'),
                                  ('electrique', 'Électrique'), ], string='Carburant')
    nombre_deplace = fields.Char(string='Nombre de places')
    nombre_de_porte = fields.Char(string='Nombre de portes')
    nombre_de_bagage = fields.Char(string='Nombre de bagages')
    climatisation = fields.Selection([('yes', 'Oui'), ('no', 'Non')], string='Climatisée')
    boite_vitesse = fields.Selection([('manuelle', 'Manuelle'),
                                      ('automatique', 'Automatique')], string='Boite Vitesse')
    description_fr = fields.Text(string='Description (FR)')
    description_en = fields.Text(string='Description (EN)')
    description_ar = fields.Text(string='Description (AR)')
    marketing_text_fr = fields.Char(string='Marketing Text (FR)')
    marketing_text_en = fields.Char(string='Marketing Text (EN)')
    marketing_text_ar = fields.Char(string='Marketing Text (AR)')
    condition_fr = fields.Text(string='Condition (FR)')
    condition_en = fields.Text(string='Condition (EN)')
    recommendation = fields.Selection([('yes', 'Oui'), ('no', 'Non')], string='Recommandation', default='no')
    categorie = fields.Many2one('categorie', string='Categorie')
    photo = fields.Binary(string='Photo', attachment=False)
    photo_ids = fields.Many2many('ir.attachment', string='Photos')
    vehicule_ids = fields.One2many('vehicule', 'modele', string='Véhicules')
    photo_link = fields.Char(string='Lien  photo')
    photo_link_nd = fields.Char(string='Lien 2eme photo')
    photo_link_pay = fields.Char(string='Lien photo paiement')
    stickers = fields.Selection([('new', 'New'),
                                 ('promotion', 'promotion'),
                                 ('normal', 'Normal')], string='autocollant', default="normal")
    vehicule_type = fields.Selection([('citadine', 'CITADINE'),
                                      ('cross', 'CROSS'),
                                      ('7_place', '7 PLACE'),
                                      ('9_place', '9 PLACE'),
                                      ('sedan', 'SEDAN'),
                                      ('compact', 'COMPACT')], string='Type de véhicule')

    def action_open_create_vehicule(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ajouter un véhicule',
            'res_model': 'vehicule',
            'view_mode': 'form',
            'view_id': self.env.ref('gestion_du_parc.view_vehicule_popup_form').id,
            'view_type': 'form',
            'context': {
                'default_modele': self.id,
            },
            'target': 'new',
        }
