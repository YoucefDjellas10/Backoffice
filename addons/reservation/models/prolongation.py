from odoo import fields, models, api, exceptions
import random
from datetime import datetime, timedelta


class Prolongation(models.Model):
    _name = 'prolongation'
    _description = 'prolongation des reservation'
    _rec_name = 'reservation'

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, default='New')
    stage = fields.Selection([('en_attend', 'En Attend'),
                              ('confirme', 'Confifrmé')], string='Status', default='en_attend')
    reservation = fields.Many2one('reservation', string='Reservation')
    status = fields.Selection(string='Etat de confirmation', related='reservation.status', store=True)
    etat_reservation = fields.Selection(string='Etat de reservation', related='reservation.etat_reservation',
                                        store=True)
    date_heure_debut = fields.Datetime(string='Date heure debut', related='reservation.date_heure_debut', store=True)
    date_heure_fin = fields.Datetime(string='Date heure fin', related='reservation.date_heure_fin', store=True)
    nbr_jour_reservation = fields.Integer(string='Durée', related='reservation.nbr_jour_reservation', store=True)
    duree_dereservation = fields.Char(string='Durée', related='reservation.duree_dereservation', store=True)

    lieu_depart = fields.Many2one(string='Lieu de départ', related='reservation.lieu_depart', store=True)
    zone = fields.Many2one(string='Zone de depart', related='reservation.zone', store=True)
    lieu_retour = fields.Many2one(string='Lieu de retour', related='reservation.lieu_retour', store=True)
    vehicule = fields.Many2one(string='Véhicule', related='reservation.vehicule', store=True)
    modele = fields.Many2one(string='Modele', related='reservation.modele', store=True)
    categorie = fields.Many2one(string='categorie', related='reservation.categorie', store=True)

    prix_jour = fields.Integer(string='Prix par jours', related='reservation.prix_jour', store=True)
    prix_jour_two = fields.Integer(string='Prix Jour Two', related='reservation.prix_jour_two', store=True)
    nbr_jour_two = fields.Integer(string='Nombre de Jours Two', related='reservation.nbr_jour_two', store=True)
    nbr_jour_one = fields.Integer(string='Nombre de Jours One', related='reservation.nbr_jour_one', store=True)
    frais_de_livraison = fields.Integer(string='Frais de livraison', related='reservation.frais_de_livraison', store=True)
    options = fields.Many2many(string='Options', related='reservation.options')
    options_total = fields.Integer(string='Total des options', related='reservation.options_total', store=True)
    total = fields.Integer(string='Total Général', related='reservation.total', store=True)
    total_afficher = fields.Integer(string='Total Afficher', related='reservation.total_afficher', store=True)
    prix_jour_afficher = fields.Float(string='Prix par jour Afficher', related='reservation.prix_jour_afficher', store=True)
    supplements = fields.Integer(string='Supplements', related='reservation.supplements', store=True)
    retour_tard = fields.Integer(string='Retour tard', related='reservation.retour_tard', store=True)

    date_prolonge = fields.Datetime(string='Date prolongée')
    nb_jour_prolonge = fields.Integer(string='Jour prolongé', compute='_compute_nb_jour_prolonge', store=True)
    heure_prolonge = fields.Integer(string='Heure prolongé', compute='_compute_heure_prolonge', store=True)
    nb_jour_prolonge_l = fields.Char(string='Jour prolongé', compute='_compute_prolongation_labels', store=True)
    heure_prolonge_l = fields.Char(string='Heure prolongé', compute='_compute_prolongation_labels', store=True)
    prix_prolongation = fields.Integer(string='Prix de prolongation', compute='_compute_prix_prolongation', store=True)
    total_option_prolonge = fields.Integer(string='Total options', compute='_compute_total_option_prolonge', store=True)
    total_prolongation = fields.Integer(string='Total Prolongation', compute='_compute_total_prolongation', store=True)
    supplements_prolonge = fields.Integer(string='Supplements Prolongés', compute='_compute_supplements', store=True)

    date_fin_un = fields.Datetime(string='Anciene date fin')
    devise = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env['res.currency'].browse(125).id)
    prix_prolongation_devise = fields.Monetary(string='Prix de prolongation', currency_field='devise',
                                               compute='_compute_prix_prolongation_devise', store=True)

    date_du_au = fields.Char(string='Anciennes dates', readonly=True)
    date_du_au_new = fields.Char(string='Nouvelles dates', readonly=True)
    effectuer_par = fields.Many2one('res.users', string='Effectuer pas', readonly=True)
    date_prolongation = fields.Datetime(string='Date de prolongation')

    def action_verifier_disponibilite(self):
        for record in self:
            if record.date_fin_un and record.date_prolonge:
                # Find reservations for the same vehicle within the specified date range
                conflicting_reservations = self.env['reservation'].search([
                    ('vehicule', '=', record.vehicule.id),
                    ('date_heure_debut', '<=', record.date_prolonge),
                    ('date_heure_fin', '>=', record.date_fin_un),
                    ('id', '!=', record.reservation.id)
                ])

                if conflicting_reservations:
                    # Créer un enregistrement temporaire pour la popup de conflit
                    popup_record = self.env['popup.confirmation'].create({
                        'message': "Le véhicule n'est pas disponible pendant la période prolongée.",
                        'popup_type': 'conflit',
                        'original_record_id': record.id,
                        'original_model': record._name,
                    })

                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Conflit de Réservation',
                        'res_model': 'popup.confirmation',
                        'res_id': popup_record.id,
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {'default_popup_type': 'conflit'}
                    }
                else:
                    # Créer un enregistrement temporaire pour la popup de disponibilité
                    popup_record = self.env['popup.confirmation'].create({
                        'message': "Le véhicule est disponible pendant la période prolongée.",
                        'popup_type': 'disponible',
                        'original_record_id': record.id,
                        'original_model': record._name,
                    })

                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Confirmation de Disponibilité',
                        'res_model': 'popup.confirmation',
                        'res_id': popup_record.id,
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {'default_popup_type': 'disponible'}
                    }



    @api.depends('total_prolongation', 'devise')
    def _compute_prix_prolongation_devise(self):
        for record in self:
            record.prix_prolongation_devise = record.total_prolongation

    @api.model
    def default_get(self, fields):
        res = super(Prolongation, self).default_get(fields)
        if 'default_reservation' in self.env.context:
            reservation = self.env['reservation'].browse(self.env.context['default_reservation'])
            if reservation:
                res['date_fin_un'] = reservation.date_heure_fin
        return res

    def action_confirm(self):
        self.stage = 'confirme'
        self.reservation.prolonge = 'oui'
        self.reservation.date_heure_fin = self.date_prolonge

    @api.depends('date_prolonge')
    def _compute_supplements(self):
        for record in self:
            supplements_value = 0

            if record.date_prolonge:
                heure_debut_float = self._convert_to_float(record.date_prolonge + timedelta(hours=1))
            else:
                heure_debut_float = 8

            supplements = self.env['supplements'].search([])

            for supplement in supplements:
                if supplement.heure_debut_float <= heure_debut_float < supplement.heure_fin_float:
                    supplements_value += supplement.montant

            record.supplements_prolonge = supplements_value

    def _convert_to_float(self, heure_datetime):
        return heure_datetime.hour + heure_datetime.minute / 60

    @api.depends('total_option_prolonge', 'prix_prolongation', 'supplements_prolonge')
    def _compute_total_prolongation(self):
        for record in self:
            record.total_prolongation = record.total_option_prolonge + record.prix_prolongation + record.supplements_prolonge

    @api.depends('options', 'nb_jour_prolonge')
    def _compute_total_option_prolonge(self):
        for record in self:
            total = 0
            for option in record.options:
                if option.type_tarif == 'jour':
                    total += option.prix * record.nb_jour_prolonge
            record.total_option_prolonge = total

    @api.depends('nb_jour_prolonge', 'heure_prolonge')
    def _compute_prolongation_labels(self):
        for record in self:
            record.nb_jour_prolonge_l = f"{record.nb_jour_prolonge} jours"
            record.heure_prolonge_l = f"{record.heure_prolonge} heures"

    @api.depends('prix_jour', 'prix_jour_two', 'retour_tard', 'heure_prolonge', 'nb_jour_prolonge')
    def _compute_prix_prolongation(self):
        for record in self:
            prix_prolongation = 0
            if record.retour_tard == 0:
                if record.heure_prolonge > 3:
                    if record.prix_jour_two == 0:
                        prix_prolongation = record.prix_jour * record.nb_jour_prolonge + (2 / 3 * record.prix_jour)
                    else:
                        prix_prolongation = record.prix_jour_two * record.nb_jour_prolonge + (2 / 3 * record.prix_jour_two)
                else:
                    if record.prix_jour_two == 0:
                        prix_prolongation = record.prix_jour * record.nb_jour_prolonge
                    else:
                        prix_prolongation = record.prix_jour_two * record.nb_jour_prolonge
            else:
                if record.prix_jour_two == 0:
                    prix_prolongation = record.prix_jour * record.nb_jour_prolonge
                else:
                    prix_prolongation = record.prix_jour_two * record.nb_jour_prolonge

            record.prix_prolongation = prix_prolongation

    @api.depends('date_heure_debut', 'date_prolonge')
    def _compute_heure_prolonge(self):
        for record in self:
            if record.date_heure_debut and record.date_prolonge:
                start_datetime = fields.Datetime.from_string(record.date_heure_debut)
                end_datetime = fields.Datetime.from_string(record.date_prolonge)

                if start_datetime.time() < end_datetime.time():
                    start_time = start_datetime.hour + start_datetime.minute / 60.0
                    end_time = end_datetime.hour + end_datetime.minute / 60.0
                    record.heure_prolonge = end_time - start_time
                else:
                    record.heure_prolonge = 0.0
            else:
                record.heure_prolonge = 0.0

    @api.depends('date_prolonge', 'date_fin_un')
    def _compute_nb_jour_prolonge(self):
        for record in self:
            if record.date_prolonge and record.date_fin_un:
                date_prolonge = fields.Datetime.from_string(record.date_prolonge).date()
                date_fin_un = fields.Datetime.from_string(record.date_fin_un).date()
                diff_days = (date_prolonge - date_fin_un).days
                record.nb_jour_prolonge = diff_days
            else:
                record.nb_jour_prolonge = 0

    @api.depends('reservation')
    def _onchange_reservation(self):
        if self.reservation:
            self.date_prolonge = self.reservation.date_heure_fin

    @api.constrains('date_prolonge', 'date_fin_un')
    def _check_date_prolonge(self):
        for record in self:
            if record.date_prolonge and record.date_fin_un and record.date_prolonge < record.date_fin_un:
                raise exceptions.ValidationError("La date prolongée ne peut pas être inférieure à la date de fin.")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            if vals.get('reservation'):
                reservation = self.env['reservation'].browse(vals['reservation'])
                random_number = random.randint(0, 9)
                vals['name'] = f"{reservation.name} - P{random_number}"
        return super(Prolongation, self).create(vals)
