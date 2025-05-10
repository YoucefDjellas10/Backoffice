from odoo import fields, models, api


class Fournisseur(models.Model):
    _name = 'fournisseur'
    _description = 'la liste des fournisseurs'

    name = fields.Char(string='Nom et Prénom')
    specialite_metier = fields.Selection([
        ('mecanicien', 'Mécanicien automobile'),
        ('electricien', 'Électricien automobile'),
        ('carrossier', 'Carrossier'),
        ('peintre', 'Peintre automobile'),
        ('technicien_diagnostic', 'Technicien diagnostic automobile'),
        ('motoriste', 'Mécanicien motoriste'),
        ('preparateur', 'Préparateur automobile'),
        ('monteur_pneu', 'Monteur pneumatique'),
        ('technicien_clim', 'Technicien en climatisation automobile'),
        ('reparateur_vitrage', 'Réparateur de pare-brise et vitrages'),
        ('expert_auto', 'Expert automobile'),
        ('technicien_hybride', 'Technicien véhicules hybrides et électriques')
    ], string="Spécialité")

class MaintenanceInherit(models.Model):
    _inherit = 'maintenance.record'

    fournisseur = fields.Many2one('fournisseur', string='Fournisseur')
