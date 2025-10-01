from odoo import fields, models, api
import requests
from requests.exceptions import RequestException, HTTPError


class Prolongation(models.Model):
    _name = 'edit.reservation'
    _description = 'request for editing reservations'

    HEURE_SELECTION = [
        ('00:00', '00:00'),
        ('00:30', '00:30'),
        ('01:00', '01:00'),
        ('01:30', '01:30'),
        ('02:00', '02:00'),
        ('02:30', '02:30'),
        ('03:00', '03:00'),
        ('03:30', '03:30'),
        ('04:00', '04:00'),
        ('04:30', '04:30'),
        ('05:00', '05:00'),
        ('05:30', '05:30'),
        ('06:00', '06:00'),
        ('06:30', '06:30'),
        ('07:00', '07:00'),
        ('07:30', '07:30'),
        ('08:00', '08:00'),
        ('08:30', '08:30'),
        ('09:00', '09:00'),
        ('09:30', '09:30'),
        ('10:00', '10:00'),
        ('10:30', '10:30'),
        ('11:00', '11:00'),
        ('11:30', '11:30'),
        ('12:00', '12:00'),
        ('12:30', '12:30'),
        ('13:00', '13:00'),
        ('13:30', '13:30'),
        ('14:00', '14:00'),
        ('14:30', '14:30'),
        ('15:00', '15:00'),
        ('15:30', '15:30'),
        ('16:00', '16:00'),
        ('16:30', '16:30'),
        ('17:00', '17:00'),
        ('17:30', '17:30'),
        ('18:00', '18:00'),
        ('18:30', '18:30'),
        ('19:00', '19:00'),
        ('19:30', '19:30'),
        ('20:00', '20:00'),
        ('20:30', '20:30'),
        ('21:00', '21:00'),
        ('21:30', '21:30'),
        ('22:00', '22:00'),
        ('22:30', '22:30'),
        ('23:00', '23:00'),
        ('23:30', '23:30'),
    ]

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, default='New')
    date_depart = fields.Date(string='date depart')
    date_retour = fields.Date(string='date retour')
    heure_depart = fields.Selection(selection=HEURE_SELECTION, string='heure depart')
    heure_retour = fields.Selection(selection=HEURE_SELECTION, string='heure retour')
    reservation = fields.Many2one('reservation', string='Reservation')
    lieu_depart = fields.Many2one('lieux', string='Lieu de départ')
    lieu_retour = fields.Many2one('lieux', string='Lieu de retour')

    disponible = fields.Selection([('yes', 'yes'), ('no', 'no')], string='Diponible', default='no')
    
    def action_verify_reservation(self):
        for record in self:
           
            params = {
                'ref': record.reservation.name if record.reservation else '',
                'lieu_depart': record.lieu_depart.id if record.lieu_depart else '',
                'lieu_retour': record.lieu_retour.id if record.lieu_retour else '',
                'date_depart': record.date_depart.strftime('%Y-%m-%d') if record.date_depart else '',
                'heure_depart': record.heure_depart or '',
                'date_retour': record.date_retour.strftime('%Y-%m-%d') if record.date_retour else '',
                'heure_retour': record.heure_retour or '',
            }

            url = "https://api.safarelamir.com/verify-calculate-ma-reservation/"
            try:
                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()  # si erreur HTTP → exception
                data = response.json()
                dispo = data.get('results', [{}])[0].get('is_available', 'unknown')
                old_total = data.get('results', [{}])[0].get('old_total', 0)
                new_total = data.get('results', [{}])[0].get('new_total', 0)

                diff = float(new_total) - float(old_total)
                diff_formatted = f"{diff:.2f}"
		
                if dispo == "yes":
                    record.write({'disponible': 'yes'})
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Succès',
                            'message': f"Le véhicule est disponible. Un supplément de {diff_formatted} € doit être ajouté.",
                            'type': 'success',
                            'sticky': True,
                        }
                    }

            except Exception as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Erreur',
                        'message': f"Erreur lors de l'appel API: {str(e)}",
                        'type': 'danger',
                        'sticky': True,
                    }
                }

    def action_edit_reservation(self):
        for record in self:
            params = {
                'ref': record.reservation.name if record.reservation else '',
                'lieu_depart': record.lieu_depart.id if record.lieu_depart else '',
                'lieu_retour': record.lieu_retour.id if record.lieu_retour else '',
                'date_depart': record.date_depart.strftime('%Y-%m-%d') if record.date_depart else '',
                'heure_depart': record.heure_depart or '',
                'date_retour': record.date_retour.strftime('%Y-%m-%d') if record.date_retour else '',
                'heure_retour': record.heure_retour or '',
                'backoffice': "yes"
            }
            reservation = None
            prolongation_id = None 
            url = "https://api.safarelamir.com/verify-edit-ma-reservation/"
            response = requests.get(url, params=params, timeout=20)
            print('response : ', response)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', {})

            reservation = results.get('reservation', 'unknown')
            prolongation_id = results.get('prolongation_id', 'unknown')
            retour_avance_id = results.get('retour_avance_id', 'unknown') 

            if prolongation_id and reservation:
                prolongation_record = self.env['prolongation'].browse(prolongation_id)
                if prolongation_record.exists():
                    prolongation_record.effectuer_par = self.env.user

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Succès',
                        'message': "Modification effectuer avec succé",
                        'type': 'success',
                        'sticky': True,
                    }
                }

            elif retour_avance_id and reservation:
                retour_avance_record = self.env['retour.avance'].browse(prolongation_id)
                if retour_avance_record.exists():
                    retour_avance_record.effectuer_par = self.env.user

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Succès',
                        'message': "Modification effectuer avec succé",
                        'type': 'success',
                        'sticky': True,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Erreur',
                        'message': "pas de reservation ou prollongation",
                        'type': 'danger',
                        'sticky': True,
                    }
                }
