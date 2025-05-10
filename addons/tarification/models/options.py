from odoo import fields, models


class Options(models.Model):
    _name = 'options'
    _description = 'les options choisi'

    name = fields.Char(string='Nom de l option', required=True)
    name_en = fields.Char(string='option name ', required=True)
    name_ar = fields.Char(string='option name AR', required=True)
    type_option = fields.Many2one('type.options', string='Type de l option', required=True)
    description = fields.Text(string='Description')
    tout_modele = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string='Appliquer sur tout les catégories',
                                   default='oui', required=True)
    modele = fields.Many2one('modele', string='Modèle')
    categorie = fields.Many2one('categorie', string='Catégorie')
    prix = fields.Integer(string='Prix')
    type_tarif = fields.Selection([('jour', 'Par jour'), ('fixe', 'Montant fixe'), ('un_jour', 'prix un jour')], string='Type de Tarif',
                                  default='jour', required=True)
    option_code = fields.Char(string='CODE', unique=True, required=True)
    caution = fields.Integer(string='caution')
    limit_Klm = fields.Integer(string='Limit KM')
    penalite_Klm = fields.Float(string='Pénalité KM')

