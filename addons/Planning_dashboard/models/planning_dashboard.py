from datetime import datetime, timedelta
from odoo import models, fields,api


class PlanningDashboard(models.Model):
    _name = 'planning.dashboard'
    _description = 'Pzlanning Dashboard'

    name = fields.Char(string="Nom de l'événement", required=True)
    date = fields.Date(string="Date de l'événement")
    description = fields.Text(string="Description")

    def get_all_zones(self):
        zones = self.env['zone'].search([])
        return [{'id': zone.id, 'name': zone.name} for zone in zones]

    def get_all_modele(self):
        modele_records = self.env['modele'].search([])
        return [{'id': modele.id, 'name': modele.name} for modele in modele_records]

    def get_all_matricules(self):
        vehicules = self.env['vehicule'].search([])
        return [{'id': vehicule.id, 'matricule': vehicule.matricule} for vehicule in vehicules]

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

        today = fields.Datetime.now().date()

        for record in vehicule_records:
            modele = record.modele.name
            if modele not in grouped_vehicles:
                grouped_vehicles[modele] = []

            planning = {}

            current_date = start_date
            while current_date <= end_date:
                day_str = current_date.strftime("%d/%m")  # Format "16/02"
                planning[day_str] = ["0", "0"]  # Initialiser chaque jour avec deux entrées
                current_date += timedelta(days=1)

            reservations = self.env['reservation'].search([
                ('vehicule', '=', record.id),
                ('date_heure_debut', '<=', end_date.strftime("%Y-%m-%d 23:59:59")),
                ('date_heure_fin', '>=', start_date.strftime("%Y-%m-%d 00:00:00"))
            ])

            for reservation in reservations:
                start_res = reservation.date_heure_debut
                end_res = reservation.date_heure_fin
                etat_reservation = reservation.etat_reservation  # Récupérer l'état de la réservation

                for day in planning.keys():
                    check_date = datetime.strptime(f"{day}/{selected_year}", "%d/%m/%Y").date()
                    if start_res.date() <= check_date <= end_res.date():
                        status = etat_reservation  # Utiliser l'état de réservation directement

                        # Jour de début
                        if check_date == start_res.date():
                            planning[day][1] = f"{status} {start_res.strftime('%H:%M')}"  # Deuxième entrée

                        # Jour de retour
                        elif check_date == end_res.date():
                            planning[day][0] = f"{status} {end_res.strftime('%H:%M')}"  # Première entrée

                        # Jour entre début et fin
                        else:
                            planning[day][0] = status  # Première entrée
                            planning[day][1] = status  # Deuxième entrée

            days_str = ", ".join([
                f"[{date} = {planning[date][0]}, {date} = {planning[date][1]}]"
                for date in planning.keys()
            ])
            details = f"id = {record.id}, matricule = {record.matricule}, Numero = {record.numero}"
            grouped_vehicles[modele].append(f"{{ {details}, {days_str} }}")

        result = [f"{modele} : {', '.join(vehicules)}" for modele, vehicules in grouped_vehicles.items()]
        print('\n'.join(result))

        return '\n'.join(result)

    def action_search_reservations(self, filters=None):
        domain = []

        # Cas 1: Premier chargement (filters=None) → 3 derniers jours
        if filters is None:
            three_days_ago = datetime.now() - timedelta(days=3)
            domain.append(('create_date', '>=', three_days_ago.strftime('%Y-%m-%d 00:00:00')))

        # Cas 2: Recherche cliquée (filters={}) → Toutes les réservations
        elif isinstance(filters, dict):
            # On applique seulement les filtres si ils existent
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
                selected_date = filters[
                    'date_debut_reservation']  # Changé de 'date_creation' à 'date_debut_reservation'
                domain.extend([
                    ('date_heure_debut', '>=', selected_date + ' 00:00:00'),
                    ('date_heure_debut', '<=', selected_date + ' 23:59:59')
                ])
            if filters.get('date_du'):
                domain.append(('create_date', '>=', filters['date_du'] + ' 00:00:00'))
            if filters.get('date_au'):
                domain.append(('create_date', '<=', filters['date_au'] + ' 23:59:59'))

        reservations = self.env['reservation'].search(domain)

        # Grouper les réservations par jour
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
                reservation.name,  # reference
                client,  # client
                datetime_str,  # date création
                date_debut_str,  # date début
                duree,  # durée
                modele,  # modèle
                zone,  # zone
                total_reduit_euro,  # total
                reservation.id,  # ID de réservation
                reservation.status  # Statut (ajouté)

            ])

        # Afficher les réservations dans le log (optionnel)
        for day, reservations_list in reservations_by_day.items():
            print(f"{day}:")
            print("{ " + ", ".join(
                [
                    f"[{ref}, {client}, {date_creation}, {date_debut}, {duree}, {modele}, {zone}, {total}, {res_id}, {status}]"
                    for ref, client, date_creation, date_debut, duree, modele, zone, total, res_id, status
                    in reservations_list]) + " }")

        return reservations_by_day