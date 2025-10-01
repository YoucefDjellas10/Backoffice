from odoo import models, fields, api
from odoo.exceptions import AccessError


class HistoriqueModification(models.Model):
    _name = 'historique.modification'
    _description = 'Journal des Modifications'
    _order = 'create_date DESC'
    _auto = True

    _sql_constraints = [
        ('check_model_id', 'CHECK(model_id >= 0)', 'ID doit être positif')
    ]

    date_modification = fields.Datetime(string="Date de modification", default=lambda self: fields.Datetime.now())
    user_id = fields.Many2one('res.users', string="Utilisateur", default=lambda self: self.env.user)
    model_name = fields.Char(string="Nom technique du modèle", required=True)
    model_id = fields.Integer(string="ID de l'enregistrement", required=True)
    field_name = fields.Char(string="Nom technique du champ", required=True)
    old_value = fields.Text(string="Valeur précédente")
    new_value = fields.Text(string="Nouvelle valeur")

    model_display_name = fields.Char(string="Modèle", compute='_compute_display_names', store=True)
    field_display_name = fields.Char(string="Champ modifié", compute='_compute_display_names', store=True)
    old_value_display = fields.Text(string="Ancienne valeur", compute='_compute_display_names')
    new_value_display = fields.Text(string="Nouvelle valeur", compute='_compute_display_names')

    @api.depends('model_name', 'field_name', 'old_value', 'new_value')
    def _compute_display_names(self):
        model_mapping = {
            'lite.atente': "Liste d'attente",
        }

        field_mapping = {
            'lieu_depart': "Lieu de départ",
            'lieu_retour': "Lieu de retour",
            'date_depart': "Date de départ",
            'date_retour': "Date de retour",
            'heure_debut': "Heure de début",
            'heure_fin': "Heure de fin",
            'statuu': "Statut",
        }

        for record in self:
            record.model_display_name = model_mapping.get(record.model_name, record.model_name)

            if record.field_name in field_mapping:
                record.field_display_name = field_mapping[record.field_name]
            else:
                record.field_display_name = record.field_name.replace('_', ' ').capitalize()

            record.old_value_display = record.old_value
            record.new_value_display = record.new_value

            if record.field_name == 'statuu' and record.old_value:
                status_mapping = {
                    'en_attente': "En attente",
                    'expire': "Expiré",
                    'offre_envoye': "Offre envoyée",
                    'reserver': "Réservé",
                    'annuler': "Annulé",
                    'trouver_ailleurs': "Trouvé ailleurs",
                    'pas_reponse': "Pas de réponse"
                }
                if record.old_value in status_mapping:
                    record.old_value_display = status_mapping[record.old_value]
                if record.new_value in status_mapping:
                    record.new_value_display = status_mapping[record.new_value]

    def _check_access(self, mode='read'):
        if not self.env.user.has_group('base.group_user'):
            raise AccessError("Accès refusé")
