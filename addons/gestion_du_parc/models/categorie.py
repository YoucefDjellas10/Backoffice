from odoo import fields, models


class Categorie(models.Model):
    _name = 'categorie'
    _description = 'categorie des modeles'

    name = fields.Char(string='Catégorie')
    show_order = fields.Integer(string='Ordre d affichage')
    caution_classic = fields.Float(string='Caution classique', digits=(6, 2))
    caution_red = fields.Float(string='Caution Réduite', digits=(6, 2))
    modele_ids = fields.One2many('modele', 'categorie', string='Modèles')
