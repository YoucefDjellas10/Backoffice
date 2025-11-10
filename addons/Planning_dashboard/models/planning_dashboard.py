from datetime import datetime, timedelta
from odoo import models, fields, api


class PlanningDashboard(models.Model):
    _name = 'planning.dashboard'
    _description = 'Planning Dashboard'

    name = fields.Char(string="Nom de l'événement", required=True)
    date = fields.Date(string="Date de l'événement")
    description = fields.Text(string="Description")

    def get_all_zones(self):
        zones = self.env['zone'].search([])
        return [{'id': zone.id, 'name': zone.name} for zone in zones]

    def get_all_modele(self):
        modele_records = self.env['modele'].search([])
        return [{'id': modele.id, 'name': modele.name} for modele in modele_records]

    @api.model
    def get_all_maintenance_types(self):
        types = self.env['type.maintenance.record'].search([])
        return [{'id': t.id, 'name': t.name} for t in types]

    def get_all_vehicule(self):
        vehicule_records = self.env['vehicule'].search([])
        return [{'id': vehicule.id, 'name': vehicule.numero} for vehicule in vehicule_records]

    def get_availibality_planning(self, *args, **kwargs):
        zone_id = int(kwargs.get('zone_id', 0)) if kwargs.get('zone_id') else None
        model_id = int(kwargs.get('model_id', 0)) if kwargs.get('model_id') else None
        selected_month = int(kwargs.get('selected_month', 0)) if kwargs.get('selected_month') else None
        selected_year = int(kwargs.get('selected_year', 0)) if kwargs.get('selected_year') else None
        start_day = int(kwargs.get('start_day', 1)) if kwargs.get('start_day') else 1

        domain = [('zone', '=', zone_id)]
        if model_id:
            domain.append(('modele', '=', model_id))

        vehicule_records = self.env['vehicule'].search(domain)
        grouped_vehicles = {}

        if not selected_month or not selected_year:
            today = fields.Datetime.now()
            selected_month = today.month
            selected_year = today.year

        start_date = datetime(selected_year, selected_month, start_day)
        end_date = start_date + timedelta(days=14)  # 15 jours au total

        # RÉCUPÉRER LES VÉHICULES BLOQUÉS POUR CETTE PÉRIODE
        blocked_vehicles = self.env['block.car'].get_blocked_vehicles_for_period(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        for record in vehicule_records:
            modele = record.modele.name
            if modele not in grouped_vehicles:
                grouped_vehicles[modele] = []

            planning = {}

            current_date = start_date
            while current_date <= end_date:
                day_str = current_date.strftime("%d/%m")
                planning[day_str] = ["0", "0"]
                current_date += timedelta(days=1)

            # APPLIQUER D'ABORD LES BLOCAGES (PRIORITÉ SUR LES RÉSERVATIONS)
            if record.id in blocked_vehicles:
                for block_info in blocked_vehicles[record.id]:
                    block_start = datetime.strptime(str(block_info['date_from']), '%Y-%m-%d').date()
                    block_end = datetime.strptime(str(block_info['date_to']), '%Y-%m-%d').date()

                    current_check_date = max(block_start, start_date.date())
                    end_check_date = min(block_end, end_date.date())

                    while current_check_date <= end_check_date:
                        day_str = current_check_date.strftime("%d/%m")

                        if day_str in planning:
                            # Marquer comme BLOQUE avec métadonnées pour le frontend
                            planning[day_str][0] = "BLOQUE"
                            planning[day_str][1] = "BLOQUE"

                        current_check_date += timedelta(days=1)

            # TRAITER LES RÉSERVATIONS (NE PAS ÉCRASER LES BLOCAGES)
            reservations = self.env['reservation'].search([
                ('vehicule', '=', record.id),
                ('date_heure_debut', '<=', end_date.strftime("%Y-%m-%d 23:59:59")),
                ('date_heure_fin', '>=', start_date.strftime("%Y-%m-%d 00:00:00")),
                ('status', '=', 'confirmee')
            ])

            for reservation in reservations:
                start_res = reservation.date_heure_debut
                end_res = reservation.date_heure_fin
                etat_reservation = reservation.etat_reservation

                current_check_date = max(start_res.date(), start_date.date())
                end_check_date = min(end_res.date(), end_date.date())

                while current_check_date <= end_check_date:
                    day_str = current_check_date.strftime("%d/%m")

                    if day_str in planning:
                        # VÉRIFIER SI CE JOUR N'EST PAS DÉJÀ BLOQUÉ
                        if planning[day_str][0] != "BLOQUE" and planning[day_str][1] != "BLOQUE":
                            status = etat_reservation

                            heure_depart = reservation.heure_depart_char or "00:00"
                            heure_retour = reservation.heure_retour_char or "00:00"

            
                            if current_check_date == start_res.date():
                                planning[day_str][1] = f"{status} {heure_depart}"

           
                            elif current_check_date == end_res.date():
                                planning[day_str][0] = f"{status} {heure_retour}"

                            # Jour entre début et fin
                            else:
                                planning[day_str][0] = status
                                planning[day_str][1] = status

                    current_check_date += timedelta(days=1)

            days_str = ", ".join([
                f"[{date} = {planning[date][0]}, {date} = {planning[date][1]}]"
                for date in planning.keys()
            ])
            details = f"id = {record.id}, matricule = {record.matricule}, Numero = {record.numero}"
            grouped_vehicles[modele].append(f"{{ {details}, {days_str} }}")

        result = [f"{modele} : {', '.join(vehicules)}" for modele, vehicules in grouped_vehicles.items()]
        print('\n'.join(result))

        return '\n'.join(result)

    # Dans planning_dashboard.py
    @api.model
    def check_vehicle_availability(self, vehicule_id, date_from, date_to):
        """
        Vérifie si un véhicule est disponible pour une période donnée
        """
        return self.env['block.car'].check_vehicle_availability(vehicule_id, date_from, date_to)
    # Reste du code inchangé...
    def action_search_reservations(self, filters=None):
        domain = []

        if filters is None:
            three_days_ago = datetime.now() - timedelta(days=3)
            domain.append(('create_date', '>=', three_days_ago.strftime('%Y-%m-%d 00:00:00')))

        elif isinstance(filters, dict):
            if filters.get('reference'):
                domain.append(('name', 'ilike', filters['reference']))
            if filters.get('prenom'):
                domain.append(('client.name', 'ilike', filters['prenom']))
            if filters.get('nom'):
                domain.append(('client.name', 'ilike', filters['nom']))
            if filters.get('modeles'):
                domain.append(('modele.id', '=', int(filters['modeles'])))
            if filters.get('pays'):
                domain.append(('zone.id', '=', int(filters['pays'])))
            if filters.get('etat'):
                domain.append(('status', '=', filters['etat']))
            if filters.get('email'):
                domain.append(('client.email', 'ilike', filters['email']))
            if filters.get('date_debut_reservation'):
                selected_date = filters['date_debut_reservation']
                domain.extend([
                    ('date_heure_debut', '>=', selected_date + ' 00:00:00'),
                    ('date_heure_debut', '<=', selected_date + ' 23:59:59')
                ])
            if filters.get('date_du'):
                domain.append(('create_date', '>=', filters['date_du'] + ' 00:00:00'))
            if filters.get('date_au'):
                domain.append(('create_date', '<=', filters['date_au'] + ' 23:59:59'))

        reservations = self.env['reservation'].search(domain)

        reservations_by_day = {}
        for reservation in reservations:
            create_date = reservation.create_date
            day_str = create_date.strftime('%d/%m')
            if day_str not in reservations_by_day:
                reservations_by_day[day_str] = []

            datetime_str = create_date.strftime('%Y-%m-%d %H:%M')
            date_debut_str = reservation.date_heure_debut_format
            duree = reservation.duree_dereservation
            modele = reservation.modele.name if reservation.modele else "N/A"
            zone = reservation.zone.name if reservation.zone else "N/A"
            client = reservation.client.name if reservation.client else "N/A"
            total_reduit_euro = reservation.total_reduit_euro if reservation.total_reduit_euro else 0

            reservations_by_day[day_str].append([
                reservation.name,
                client,
                datetime_str,
                date_debut_str,
                duree,
                modele,
                zone,
                total_reduit_euro,
                reservation.id,
                reservation.status
            ])

        for day, reservations_list in reservations_by_day.items():
            print(f"{day}:")
            print("{ " + ", ".join(
                [
                    f"[{ref}, {client}, {date_creation}, {date_debut}, {duree}, {modele}, {zone}, {total}, {res_id}, {status}]"
                    for ref, client, date_creation, date_debut, duree, modele, zone, total, res_id, status
                    in reservations_list]) + " }")

        return reservations_by_day
