from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime


class DepenseRecord(models.Model):
    _name = 'depense.record'
    _description = 'Dépenses'

    name = fields.Char(string='id', readonly=True, copy=False)
    type_depense = fields.Many2one('type.depens', string='Type de dépense')
    zone = fields.Many2one(string='zone', related='caisse.zone', store=True)
    caisse = fields.Many2one('caisse.record', string='Caisse')
    maintenance = fields.Many2one('maintenance.record', string='Maintenance')
    vehicule = fields.Many2one(string='Véhicule', related='maintenance.vehicule_id')
    type_maintenance_id = fields.Many2one(string='Maintenance', related='maintenance.type_maintenance_id')
    euro = fields.Many2one('res.currency', string='euro',
                           default=lambda self: self.env['res.currency'].browse(125).id)
    dinar = fields.Many2one('res.currency', string='Dinar algérien',
                            default=lambda self: self.env['res.currency'].browse(111).id)
    montant_da = fields.Monetary(string='Montant DA', currency_field='dinar')
    montant_eur = fields.Monetary(string='Montant €', currency_field='euro',
                                  compute='_compute_montant_eur', strore=True)
    vehicule_numero = fields.Many2one('vehicule', string='Vehicule')
    note = fields.Text(string='Note')
    status = fields.Selection([('en_attente', 'en attente'),
                               ('valde_mr', 'Validé par MR'),
                               ('valide_mg', 'Validé par MG'),
                               ('annule', 'Annulé'),
                               ('valide', 'Validé')], string='Etat', default='en_attente')


    carburant_motif = fields.Selection([('plein_client', 'Plein client'),
                                        ('complement', 'Complément'),
                                        ('service', 'Service'),
                                        ('mission', 'Mission'),
                                        ('autre', 'Autre'),],string='Justif. carburant')

    date_de_realisation = fields.Date(string='Date de realisation', default=fields.Date.today)
    manager_note = fields.Text(string='Note Manager')

    hors_zone = fields.Selection([('oui', 'Oui'),
                                  ('non', 'Non')],string='Hors zone', default="non")
    vehicule_hors_zone = fields.Many2one('vehicule', string='vehicule hors zone', compute='_compute_vehicule_hors_zone', store=True)
    matricule_numero = fields.Char(string='Matricule ou Numero')

    @api.depends('hors_zone', 'matricule_numero')
    def _compute_vehicule_hors_zone(self):
        for record in self:
            if record.hors_zone == 'oui' and record.matricule_numero:
                vehicule = self.env['vehicule'].search([('numero', '=', record.matricule_numero)], limit=1)
                if not vehicule:
                    vehicule = self.env['vehicule'].search([('matricule', '=', record.matricule_numero)], limit=1)

                if vehicule:
                    record.vehicule_hors_zone = vehicule.id
                else:
                    record.vehicule_hors_zone = False
            else:
                record.vehicule_hors_zone = False

    @api.constrains('hors_zone', 'matricule_numero', 'vehicule_hors_zone')
    def _check_vehicule_hors_zone(self):
        for record in self:
            if record.hors_zone == 'oui' and record.matricule_numero:
                if not record.vehicule_hors_zone:
                    raise ValidationError(
                        f"Le véhicule avec le matricule/numéro '{record.matricule_numero}' "
                        "n'existe pas dans la base de données. Veuillez vérifier le matricule ou le numéro."
                    )

    def action_annuler(self):
        self.status = 'annule'

    def action_valide_mr(self):
        self.status = 'valde_mr'

    def action_valide_mg(self):
        self.status = 'valide_mg'

    def action_valide(self):
        self.status = 'valide'

    @api.depends('montant_da', 'montant_eur')
    def _compute_montant_eur(self):
        for record in self:
            taux_change = self.env['taux.change'].search([('id', '=', 2)], limit=1)
            if taux_change:
                taux = taux_change.montant
                record.montant_eur = record.montant_da / taux
            else:
                record.montant_eur = 0

    @api.model
    def create(self, vals):
        record = super(DepenseRecord, self).create(vals)
        record.name = 'dépense-{:02d}'.format(record.id)
        return record

    
    @api.model
    def action_search_depenses(self, filters=None, page=1, limit=30):
        """
        Recherche des dépenses avec filtres
        """
        domain = []

        if filters:
            # Filtrage par mois et année (obligatoires)
            if filters.get('mois') and filters.get('annee'):
                start_date = datetime(filters['annee'], filters['mois'], 1)
                if filters['mois'] == 12:
                    end_date = datetime(filters['annee'] + 1, 1, 1)
                else:
                    end_date = datetime(filters['annee'], filters['mois'] + 1, 1)

                domain.append(('create_date', '>=', start_date.strftime('%Y-%m-%d 00:00:00')))
                domain.append(('create_date', '<', end_date.strftime('%Y-%m-%d 00:00:00')))

            # Filtres optionnels
            if filters.get('zone'):
                domain.append(('zone.id', '=', filters['zone']))
            if filters.get('type_depense'):
                domain.append(('type_depense.id', '=', filters['type_depense']))
            if filters.get('vehicule'):
                domain.append(('vehicule_numero.id', '=', filters['vehicule']))
            if filters.get('statut'):
                domain.append(('status', '=', filters['statut']))

        # Pagination
        offset = (page - 1) * limit
        

        # Recherche avec pagination
        depenses = self.search(domain, limit=limit, offset=offset, order='date_de_realisation desc')
        total_count = self.search_count(domain)

        # ✅ Calcul du total global des montants (toutes les dépenses filtrées)
        total_montant = sum(dep.montant_da for dep in self.search(domain))

        # Données pour le frontend
        depenses_data = []
        for depense in depenses:
            depenses_data.append({
                'id': depense.id,
                'name': depense.name or '',
                'type_depense': depense.type_depense.name if depense.type_depense else 'N/A',
                'montant_da': f"{depense.montant_da:.2f}" if depense.montant_da else '0.00',
                'montant_eur': f"{depense.montant_eur:.2f}" if depense.montant_eur else '0.00',
                'vehicule': depense.vehicule_numero.numero if depense.vehicule_numero else 'N/A',
                'caisse': depense.caisse.user_id.name if depense.caisse else 'N/A',
                'zone': depense.zone.name if depense.zone else 'N/A',
                'status_display': dict(depense._fields['status'].selection).get(depense.status, 'N/A'),
                'statut': depense.status,
                'create_date': depense.create_date.strftime('%d/%m/%Y %H:%M') if depense.create_date else '',
                'date_de_realisation': depense.date_de_realisation.strftime(
                    '%d/%m/%Y') if depense.date_de_realisation else '',
            })
        return {
            'depenses': depenses_data,
            'total_count': total_count,
            'total_montant': total_montant,  # ✅ Ajout du total
        }
