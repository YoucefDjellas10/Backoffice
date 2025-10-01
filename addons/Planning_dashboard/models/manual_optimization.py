from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ManualOptimization(models.Model):  # Changé de TransientModel à Model
    _name = 'manual.optimization'
    _description = 'Optimisation manuelle des réservations'
    _order = 'create_date desc'  # Tri par date de création décroissante

    date_from = fields.Date(string="Du", required=True)
    date_to = fields.Date(string="Au", required=True)

    vehicule_actuel = fields.Selection(
        selection=lambda self: self.get_all_vehicule(),
        string="Véhicule actuel",
        required=True
    )
    vehicule_changer = fields.Selection(
        selection=lambda self: self.get_all_vehicule(),
        string="Véhicule à changer",
        required=True
    )

    # Champs computed pour afficher les noms des véhicules
    vehicule_actuel_name = fields.Char(
        string="Véhicule actuel",
        compute='_compute_vehicule_names',
        store=True
    )
    vehicule_changer_name = fields.Char(
        string="Véhicule à changer",
        compute='_compute_vehicule_names',
        store=True
    )

    # Champ pour indiquer si l'optimisation a été effectuée
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('done', 'Effectué')
    ], default='draft', string='État')

    @api.depends('vehicule_actuel', 'vehicule_changer')
    def _compute_vehicule_names(self):
        for record in self:
            if record.vehicule_actuel:
                vehicule_actuel_obj = self.env['vehicule'].browse(int(record.vehicule_actuel))
                record.vehicule_actuel_name = vehicule_actuel_obj.numero or ''
            else:
                record.vehicule_actuel_name = ''

            if record.vehicule_changer:
                vehicule_changer_obj = self.env['vehicule'].browse(int(record.vehicule_changer))
                record.vehicule_changer_name = vehicule_changer_obj.numero or ''
            else:
                record.vehicule_changer_name = ''

    @api.model
    def get_all_vehicule(self):
        vehicule_records = self.env['vehicule'].search([])
        return [(str(vehicule.id), vehicule.numero) for vehicule in vehicule_records]

    def action_validate(self):
        # Vérifier que les véhicules sont différents
        if self.vehicule_actuel == self.vehicule_changer:
            raise UserError(_("Vous ne pouvez pas transférer vers le même véhicule!"))

        # Vérifier la disponibilité du véhicule de remplacement
        if not self._check_vehicule_availability():
            raise UserError(_("Le véhicule de remplacement n'est pas disponible pendant cette période!"))

        # Effectuer le transfert
        self._transfer_reservations()

        # Marquer comme effectué
        self.state = 'done'

        # Afficher la notification et fermer le pop-up
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Succès",
                'message': "Transfert effectué avec succès.",
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}  # Ferme le pop-up
            }
        }

    def _check_vehicule_availability(self):
        """Vérifie si le véhicule de remplacement est disponible"""
        reservations = self.env['reservation'].search([
            ('vehicule', '=', int(self.vehicule_changer)),
            ('date_heure_debut', '<=', self.date_to.strftime("%Y-%m-%d 23:59:59")),
            ('date_heure_fin', '>=', self.date_from.strftime("%Y-%m-%d 00:00:00"))
        ])
        return not bool(reservations)

    def _transfer_reservations(self):
        """Transfère les réservations du véhicule actuel vers le véhicule de remplacement"""
        reservations = self.env['reservation'].search([
            ('vehicule', '=', int(self.vehicule_actuel)),
            ('date_heure_debut', '<=', self.date_to.strftime("%Y-%m-%d 23:59:59")),
            ('date_heure_fin', '>=', self.date_from.strftime("%Y-%m-%d 00:00:00"))
        ])

        for reservation in reservations:
            reservation.write({'vehicule': int(self.vehicule_changer)})
