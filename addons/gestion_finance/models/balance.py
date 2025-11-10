from odoo import models, fields, api
from datetime import datetime


class Balance(models.Model):
    _name = 'balance'
    _description = 'Balance'

    name = fields.Char(string='Nom', required=True)
    balance = fields.Float(string='Balance', digits=(12, 2))

    @api.model
    def get_balance_data(self):
        caisse_records = self.env['caisse.record'].search([])

        result = {
            'managers_generaux': [],
            'ceos': [],
            'zones': {}
        }

        region_managers = {}
        for record in caisse_records:
            if record.type_caisse == 'manager_region' and record.zone:
                zone_name = record.zone.name
                region_managers[zone_name] = {
                    'id': record.user_id.id,  # ← Utiliser l'ID de l'utilisateur
                    'record_id': record.id,   # ← Garder l'ID du record aussi si besoin
                    'name': record.user_id.name or 'Sans nom',
                    'balance': record.caisse_dzd or 0,
                    'zone_name': zone_name
                }

        for record in caisse_records:
            user_data = {
                'id': record.user_id.id,  # ← Utiliser l'ID de l'utilisateur
                'record_id': record.id,   # ← Garder l'ID du record aussi si besoin
                'name': record.user_id.name or 'Sans nom',
                'balance': record.caisse_dzd or 0,
                'zone_name': record.zone.name if record.zone else 'Sans Zone'
            }

            if record.type_caisse == 'manager_general':
                result['managers_generaux'].append(user_data)

            elif record.type_caisse == 'ceo':
                result['ceos'].append(user_data)
            elif record.type_caisse == 'agent' and record.zone:
                zone_name = record.zone.name
                if zone_name not in result['zones']:
                    result['zones'][zone_name] = {
                        'manager': region_managers.get(zone_name),
                        'agents': []
                    }
                result['zones'][zone_name]['agents'].append(user_data)
            elif record.type_caisse == 'manager_region' and record.zone:
                zone_name = record.zone.name
                if zone_name not in result['zones']:
                    result['zones'][zone_name] = {
                        'manager': region_managers.get(zone_name),
                        'agents': []
                    }
                result['zones'][zone_name]['manager'] = region_managers.get(zone_name)

        for zone_name, manager_data in region_managers.items():
            if zone_name not in result['zones']:
                result['zones'][zone_name] = {
                    'manager': manager_data,
                    'agents': []
                }

        return result

    @api.model
    def get_annual_filters(self):
        """Retourne les années disponibles"""
        current_year = datetime.now().year
        years = list(range(current_year - 5, current_year + 2))
        return {'years': years}

    @api.model
    def get_annual_balance_data(self, params):

        year = params.get('year', datetime.now().year)

        zone_id = params.get('zone')
        vehicle_id = params.get('vehicle')

        monthly_data = []

        for month in range(1, 13):
            depense_domain = [
                ('create_date', '>=', f'{year}-{month:02d}-01 00:00:00'),
                ('create_date', '<', f'{year}-{month+1:02d}-01 00:00:00' if month < 12 else f'{year+1}-01-01 00:00:00'),
                ('status', '=', 'valide'),
            ]

            if zone_id:
                depense_domain.append(('zone.id', '=', int(zone_id)))
            if vehicle_id:
                depense_domain.append(('vehicule_numero.id', '=', int(vehicle_id)))

            depenses = self.env['depense.record'].search(depense_domain)
            total_depense = sum(dep.montant_da for dep in depenses)

            recette_domain = [
                '|',
                '&',
                ('create_date', '>=', f'{year}-{month:02d}-01 00:00:00'),
                ('create_date', '<', f'{year}-{month+1:02d}-01 00:00:00' if month < 12 else f'{year+1}-01-01 00:00:00'),
                '&',
                ('create_date', '=', False),
                '&',
                ('reservation.create_date', '>=', f'{year}-{month:02d}-01 00:00:00'),
                ('reservation.create_date', '<', f'{year}-{month+1:02d}-01 00:00:00' if month < 12 else f'{year+1}-01-01 00:00:00')
            ]

            if zone_id:
                recette_domain.append(('reservation_id.zone_id.id', '=', int(zone_id)))
            if vehicle_id:
                recette_domain.append(('reservation_id.vehicule_id.id', '=', int(vehicle_id)))

            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)

            recettes = self.env['revenue.record'].search(recette_domain)
            total_recette = sum(rec.montant_dzd for rec in recettes) + sum(rec.montant * taux_change.montant for rec in recettes)

            balance = total_recette - total_depense

            monthly_data.append({
                'month': month,
                'depense': total_depense,
                'recette': total_recette,
                'balance': balance,
            })

        return {'monthly_data': monthly_data}
