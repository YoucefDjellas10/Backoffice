from odoo import models, fields, api


class PopupConfirmation(models.TransientModel):
    _name = 'popup.confirmation'
    _description = 'Popup de Confirmation'

    message = fields.Text('Message', required=True)
    popup_type = fields.Selection([
        ('conflit', 'Conflit'),
        ('disponible', 'Disponible')
    ], string='Type de Popup', required=True)

    original_record_id = fields.Integer('ID Enregistrement Original')
    original_model = fields.Char('Modèle Original')

    def action_cancel(self):
        """Action pour le bouton Annuler"""
        return {'type': 'ir.actions.act_window_close'}

    def action_confirm(self):
        """Action pour le bouton Confirmer (uniquement pour le type 'disponible')"""
        if self.popup_type == 'disponible' and self.original_record_id and self.original_model:
            # Récupérer l'enregistrement original
            original_record = self.env[self.original_model].browse(self.original_record_id)

            # Effectuer les actions de confirmation
            original_record.stage = 'confirme'
            original_record.reservation.prolonge = 'oui'
            original_record.reservation.date_heure_fin = original_record.date_prolonge

        return {'type': 'ir.actions.act_window_close'}
