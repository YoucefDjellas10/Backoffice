from odoo import fields, models, api


class Tarifs(models.Model):
    _name = 'tarifs'
    _description = 'Tarifs des modèles'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    saison = fields.Many2one('saison', string='Saison', required=True)
    periodes = fields.One2many(string='Périodes', related='saison.periodes')
    modele = fields.Many2one('modele', string='Modèle', required=True)
    categorie = fields.Many2one(string='categorie', related='modele.categorie', store=True)
    prix = fields.Integer(string='Prix')
    nb_jour = fields.Many2one('nb.jour', string='Nombre de jours', required=True)
    nbr_de = fields.Integer(string='à partir de', related='nb_jour.de', store=True)
    nbr_au = fields.Integer(string='au', related='nb_jour.au', store=True)
    date_depart_one = fields.Date(string='Date Début One', compute='_compute_date_depart_fin', store=True)
    date_fin_one = fields.Date(string='Date Fin One', compute='_compute_date_depart_fin', store=True)
    date_depart_two = fields.Date(string='Date Début Two', compute='_compute_date_depart_fin', store=True)
    date_fin_two = fields.Date(string='Date Fin Two', compute='_compute_date_depart_fin', store=True)
    date_depart_three = fields.Date(string='Date Début Three', compute='_compute_date_depart_fin', store=True)
    date_fin_three = fields.Date(string='Date Fin Three', compute='_compute_date_depart_fin', store=True)
    date_depart_four = fields.Date(string='Date Début Four', compute='_compute_date_depart_fin', store=True)
    date_fin_four = fields.Date(string='Date Fin Four', compute='_compute_date_depart_fin', store=True)

    @api.onchange('prix')
    def _onchange_prix(self):
        if self.modele:
            self.modele._compute_tarif_fields()

    @api.depends('saison', 'modele', 'nb_jour')
    def _compute_name(self):
        for record in self:
            saison_name = record.saison.name if record.saison else ''
            modele_name = record.modele.name if record.modele else ''
            nb_jour_name = record.nb_jour.name if record.nb_jour else ''
            record.name = f'{saison_name} / {modele_name} / {nb_jour_name}'

    @api.depends('periodes', 'periodes.date_debut', 'periodes.date_fin')
    def _compute_date_depart_fin(self):
        for record in self:
            periodes = record.periodes
            periodes_sorted = periodes.sorted(key=lambda p: p.date_debut)  # Triez les périodes par date de début
            if periodes_sorted:
                record.date_depart_one = periodes_sorted[0].date_debut
                record.date_fin_one = periodes_sorted[0].date_fin
            else:
                record.date_depart_one = False
                record.date_fin_one = False

            if len(periodes_sorted) > 1:
                record.date_depart_two = periodes_sorted[1].date_debut
                record.date_fin_two = periodes_sorted[1].date_fin
            else:
                record.date_depart_two = False
                record.date_fin_two = False

            if len(periodes_sorted) > 2:
                record.date_depart_three = periodes_sorted[2].date_debut
                record.date_fin_three = periodes_sorted[2].date_fin
            else:
                record.date_depart_three = False
                record.date_fin_three = False

            if len(periodes_sorted) > 3:
                record.date_depart_four = periodes_sorted[3].date_debut
                record.date_fin_four = periodes_sorted[3].date_fin
            else:
                record.date_depart_four = False
                record.date_fin_four = False


class ModeleInherit(models.Model):
    _inherit = 'modele'

    tarifs = fields.One2many('tarifs', 'modele', string='Tarifs', store=True)

    def action_open_create_tarifs(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ajouter un tarif',
            'res_model': 'tarifs',
            'view_mode': 'form',
            'view_id': self.env.ref('tarification.view_tarifs_form_popup').id,
            'view_type': 'form',
            'context': {
                'default_modele': self.id,
            },
            'target': 'new',  # opens in a new modal
        }

    nbr_de_t_one = fields.Integer(string='À partir de (Tarif 1)', compute='_compute_tarif_fields', store=True)
    nbr_au_t_one = fields.Integer(string='Au (Tarif 1)', compute='_compute_tarif_fields', store=True)
    date_depart_one_t_one = fields.Date(string='Date Début One (Tarif 1)', compute='_compute_tarif_fields', store=True)
    date_fin_one_t_one = fields.Date(string='Date Fin One (Tarif 1)', compute='_compute_tarif_fields', store=True)
    date_depart_two_t_one = fields.Date(string='Date Début Two (Tarif 1)', compute='_compute_tarif_fields', store=True)
    date_fin_two_t_one = fields.Date(string='Date Fin Two (Tarif 1)', compute='_compute_tarif_fields', store=True)
    date_depart_three_t_one = fields.Date(string='Date Début Three (Tarif 1)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_three_t_one = fields.Date(string='Date Fin Three (Tarif 1)', compute='_compute_tarif_fields', store=True)
    date_depart_four_t_one = fields.Date(string='Date Début Four (Tarif 1)', compute='_compute_tarif_fields',
                                         store=True)
    date_fin_four_t_one = fields.Date(string='Date Fin Four (Tarif 1)', compute='_compute_tarif_fields', store=True)

    nbr_de_t_two = fields.Integer(string='À partir de (Tarif 2)', compute='_compute_tarif_fields', store=True)
    nbr_au_t_two = fields.Integer(string='Au (Tarif 2)', compute='_compute_tarif_fields', store=True)
    date_depart_one_t_two = fields.Date(string='Date Début One (Tarif 2)', compute='_compute_tarif_fields', store=True)
    date_fin_one_t_two = fields.Date(string='Date Fin One (Tarif 2)', compute='_compute_tarif_fields', store=True)
    date_depart_two_t_two = fields.Date(string='Date Début Two (Tarif 2)', compute='_compute_tarif_fields', store=True)
    date_fin_two_t_two = fields.Date(string='Date Fin Two (Tarif 2)', compute='_compute_tarif_fields', store=True)
    date_depart_three_t_two = fields.Date(string='Date Début Three (Tarif 2)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_three_t_two = fields.Date(string='Date Fin Three (Tarif 2)', compute='_compute_tarif_fields', store=True)
    date_depart_four_t_two = fields.Date(string='Date Début Four (Tarif 2)', compute='_compute_tarif_fields',
                                         store=True)
    date_fin_four_t_two = fields.Date(string='Date Fin Four (Tarif 2)', compute='_compute_tarif_fields', store=True)

    nbr_de_t_three = fields.Integer(string='À partir de (Tarif 3)', compute='_compute_tarif_fields', store=True)
    nbr_au_t_three = fields.Integer(string='Au (Tarif 3)', compute='_compute_tarif_fields', store=True)
    date_depart_one_t_three = fields.Date(string='Date Début One (Tarif 3)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_one_t_three = fields.Date(string='Date Fin One (Tarif 3)', compute='_compute_tarif_fields', store=True)
    date_depart_two_t_three = fields.Date(string='Date Début Two (Tarif 3)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_two_t_three = fields.Date(string='Date Fin Two (Tarif 3)', compute='_compute_tarif_fields', store=True)
    date_depart_three_t_three = fields.Date(string='Date Début Three (Tarif 3)', compute='_compute_tarif_fields',
                                            store=True)
    date_fin_three_t_three = fields.Date(string='Date Fin Three (Tarif 3)', compute='_compute_tarif_fields', store=True)
    date_depart_four_t_three = fields.Date(string='Date Début Four (Tarif 3)', compute='_compute_tarif_fields',
                                           store=True)
    date_fin_four_t_three = fields.Date(string='Date Fin Four (Tarif 3)', compute='_compute_tarif_fields', store=True)

    nbr_de_t_four = fields.Integer(string='À partir de (Tarif 4)', compute='_compute_tarif_fields', store=True)
    nbr_au_t_four = fields.Integer(string='Au (Tarif 4)', compute='_compute_tarif_fields', store=True)
    date_depart_one_t_four = fields.Date(string='Date Début One (Tarif 4)', compute='_compute_tarif_fields', store=True)
    date_fin_one_t_four = fields.Date(string='Date Fin One (Tarif 4)', compute='_compute_tarif_fields', store=True)
    date_depart_two_t_four = fields.Date(string='Date Début Two (Tarif 4)', compute='_compute_tarif_fields', store=True)
    date_fin_two_t_four = fields.Date(string='Date Fin Two (Tarif 4)', compute='_compute_tarif_fields', store=True)
    date_depart_three_t_four = fields.Date(string='Date Début Three (Tarif 4)', compute='_compute_tarif_fields',
                                           store=True)
    date_fin_three_t_four = fields.Date(string='Date Fin Three (Tarif 4)', compute='_compute_tarif_fields', store=True)
    date_depart_four_t_four = fields.Date(string='Date Début Four (Tarif 4)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_four_t_four = fields.Date(string='Date Fin Four (Tarif 4)', compute='_compute_tarif_fields', store=True)

    nbr_de_t_five = fields.Integer(string='À partir de (Tarif 5)', compute='_compute_tarif_fields', store=True)
    nbr_au_t_five = fields.Integer(string='Au (Tarif 5)', compute='_compute_tarif_fields', store=True)
    date_depart_one_t_five = fields.Date(string='Date Début One (Tarif 5)', compute='_compute_tarif_fields', store=True)
    date_fin_one_t_five = fields.Date(string='Date Fin One (Tarif 5)', compute='_compute_tarif_fields', store=True)
    date_depart_two_t_five = fields.Date(string='Date Début Two (Tarif 5)', compute='_compute_tarif_fields', store=True)
    date_fin_two_t_five = fields.Date(string='Date Fin Two (Tarif 5)', compute='_compute_tarif_fields', store=True)
    date_depart_three_t_five = fields.Date(string='Date Début Three (Tarif 5)', compute='_compute_tarif_fields',
                                           store=True)
    date_fin_three_t_five = fields.Date(string='Date Fin Three (Tarif 5)', compute='_compute_tarif_fields', store=True)
    date_depart_four_t_five = fields.Date(string='Date Début Four (Tarif 5)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_four_t_five = fields.Date(string='Date Fin Four (Tarif 5)', compute='_compute_tarif_fields', store=True)

    nbr_de_t_six = fields.Integer(string='À partir de (Tarif 6)', compute='_compute_tarif_fields', store=True)
    nbr_au_t_six = fields.Integer(string='Au (Tarif 6)', compute='_compute_tarif_fields', store=True)
    date_depart_one_t_six = fields.Date(string='Date Début One (Tarif 6)', compute='_compute_tarif_fields', store=True)
    date_fin_one_t_six = fields.Date(string='Date Fin One (Tarif 6)', compute='_compute_tarif_fields', store=True)
    date_depart_two_t_six = fields.Date(string='Date Début Two (Tarif 6)', compute='_compute_tarif_fields', store=True)
    date_fin_two_t_six = fields.Date(string='Date Fin Two (Tarif 6)', compute='_compute_tarif_fields', store=True)
    date_depart_three_t_six = fields.Date(string='Date Début Three (Tarif 6)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_three_t_six = fields.Date(string='Date Fin Three (Tarif 6)', compute='_compute_tarif_fields', store=True)
    date_depart_four_t_six = fields.Date(string='Date Début Four (Tarif 6)', compute='_compute_tarif_fields',
                                         store=True)
    date_fin_four_t_six = fields.Date(string='Date Fin Four (Tarif 6)', compute='_compute_tarif_fields', store=True)

    nbr_de_t_seven = fields.Integer(string='À partir de (Tarif 7)', compute='_compute_tarif_fields', store=True)
    nbr_au_t_seven = fields.Integer(string='Au (Tarif 7)', compute='_compute_tarif_fields', store=True)
    date_depart_one_t_seven = fields.Date(string='Date Début One (Tarif 7)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_one_t_seven = fields.Date(string='Date Fin One (Tarif 7)', compute='_compute_tarif_fields', store=True)
    date_depart_two_t_seven = fields.Date(string='Date Début Two (Tarif 7)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_two_t_seven = fields.Date(string='Date Fin Two (Tarif 7)', compute='_compute_tarif_fields', store=True)
    date_depart_three_t_seven = fields.Date(string='Date Début Three (Tarif 7)', compute='_compute_tarif_fields',
                                            store=True)
    date_fin_three_t_seven = fields.Date(string='Date Fin Three (Tarif 7)', compute='_compute_tarif_fields', store=True)
    date_depart_four_t_seven = fields.Date(string='Date Début Four (Tarif 7)', compute='_compute_tarif_fields',
                                           store=True)
    date_fin_four_t_seven = fields.Date(string='Date Fin Four (Tarif 7)', compute='_compute_tarif_fields', store=True)

    nbr_de_t_eight = fields.Integer(string='À partir de (Tarif 8)', compute='_compute_tarif_fields', store=True)
    nbr_au_t_eight = fields.Integer(string='Au (Tarif 8)', compute='_compute_tarif_fields', store=True)
    date_depart_one_t_eight = fields.Date(string='Date Début One (Tarif 8)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_one_t_eight = fields.Date(string='Date Fin One (Tarif 8)', compute='_compute_tarif_fields', store=True)
    date_depart_two_t_eight = fields.Date(string='Date Début Two (Tarif 8)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_two_t_eight = fields.Date(string='Date Fin Two (Tarif 8)', compute='_compute_tarif_fields', store=True)
    date_depart_three_t_eight = fields.Date(string='Date Début Three (Tarif 8)', compute='_compute_tarif_fields',
                                            store=True)
    date_fin_three_t_eight = fields.Date(string='Date Fin Three (Tarif 8)', compute='_compute_tarif_fields', store=True)
    date_depart_four_t_eight = fields.Date(string='Date Début Four (Tarif 8)', compute='_compute_tarif_fields',
                                           store=True)
    date_fin_four_t_eight = fields.Date(string='Date Fin Four (Tarif 8)', compute='_compute_tarif_fields', store=True)

    nbr_de_t_nine = fields.Integer(string='À partir de (Tarif 9)', compute='_compute_tarif_fields', store=True)
    nbr_au_t_nine = fields.Integer(string='Au (Tarif 9)', compute='_compute_tarif_fields', store=True)
    date_depart_one_t_nine = fields.Date(string='Date Début One (Tarif 9)', compute='_compute_tarif_fields', store=True)
    date_fin_one_t_nine = fields.Date(string='Date Fin One (Tarif 9)', compute='_compute_tarif_fields', store=True)
    date_depart_two_t_nine = fields.Date(string='Date Début Two (Tarif 9)', compute='_compute_tarif_fields', store=True)
    date_fin_two_t_nine = fields.Date(string='Date Fin Two (Tarif 9)', compute='_compute_tarif_fields', store=True)
    date_depart_three_t_nine = fields.Date(string='Date Début Three (Tarif 9)', compute='_compute_tarif_fields',
                                           store=True)
    date_fin_three_t_nine = fields.Date(string='Date Fin Three (Tarif 9)', compute='_compute_tarif_fields', store=True)
    date_depart_four_t_nine = fields.Date(string='Date Début Four (Tarif 9)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_four_t_nine = fields.Date(string='Date Fin Four (Tarif 9)', compute='_compute_tarif_fields', store=True)

    nbr_de_t_ten = fields.Integer(string='À partir de (Tarif 10)', compute='_compute_tarif_fields', store=True)
    nbr_au_t_ten = fields.Integer(string='Au (Tarif 10)', compute='_compute_tarif_fields', store=True)
    date_depart_one_t_ten = fields.Date(string='Date Début One (Tarif 10)', compute='_compute_tarif_fields', store=True)
    date_fin_one_t_ten = fields.Date(string='Date Fin One (Tarif 10)', compute='_compute_tarif_fields', store=True)
    date_depart_two_t_ten = fields.Date(string='Date Début Two (Tarif 10)', compute='_compute_tarif_fields', store=True)
    date_fin_two_t_ten = fields.Date(string='Date Fin Two (Tarif 10)', compute='_compute_tarif_fields', store=True)
    date_depart_three_t_ten = fields.Date(string='Date Début Three (Tarif 10)', compute='_compute_tarif_fields',
                                          store=True)
    date_fin_three_t_ten = fields.Date(string='Date Fin Three (Tarif 10)', compute='_compute_tarif_fields', store=True)
    date_depart_four_t_ten = fields.Date(string='Date Début Four (Tarif 10)', compute='_compute_tarif_fields',
                                         store=True)
    date_fin_four_t_ten = fields.Date(string='Date Fin Four (Tarif 10)', compute='_compute_tarif_fields', store=True)

    @api.depends('tarifs', 'tarifs.prix')
    def _compute_tarif_fields(self):
        for record in self:
            tarifs = record.tarifs.sorted(key=lambda r: r.date_depart_one)  # Tri des tarifs par date de début

            if len(tarifs) > 0:
                record.nbr_de_t_one = tarifs[0].nbr_de
                record.nbr_au_t_one = tarifs[0].nbr_au
                record.date_depart_one_t_one = tarifs[0].date_depart_one
                record.date_fin_one_t_one = tarifs[0].date_fin_one
                record.date_depart_two_t_one = tarifs[0].date_depart_two
                record.date_fin_two_t_one = tarifs[0].date_fin_two
                record.date_depart_three_t_one = tarifs[0].date_depart_three
                record.date_fin_three_t_one = tarifs[0].date_fin_three
                record.date_depart_four_t_one = tarifs[0].date_depart_four
                record.date_fin_four_t_one = tarifs[0].date_fin_four
            else:
                record.nbr_de_t_one = False
                record.nbr_au_t_one = False
                record.date_depart_one_t_one = False
                record.date_fin_one_t_one = False
                record.date_depart_two_t_one = False
                record.date_fin_two_t_one = False
                record.date_depart_three_t_one = False
                record.date_fin_three_t_one = False
                record.date_depart_four_t_one = False
                record.date_fin_four_t_one = False

            if len(tarifs) > 1:
                record.nbr_de_t_two = tarifs[1].nbr_de
                record.nbr_au_t_two = tarifs[1].nbr_au
                record.date_depart_one_t_two = tarifs[1].date_depart_one
                record.date_fin_one_t_two = tarifs[1].date_fin_one
                record.date_depart_two_t_two = tarifs[1].date_depart_two
                record.date_fin_two_t_two = tarifs[1].date_fin_two
                record.date_depart_three_t_two = tarifs[1].date_depart_three
                record.date_fin_three_t_two = tarifs[1].date_fin_three
                record.date_depart_four_t_two = tarifs[1].date_depart_four
                record.date_fin_four_t_two = tarifs[1].date_fin_four
            else:
                record.nbr_de_t_two = False
                record.nbr_au_t_two = False
                record.date_depart_one_t_two = False
                record.date_fin_one_t_two = False
                record.date_depart_two_t_two = False
                record.date_fin_two_t_two = False
                record.date_depart_three_t_two = False
                record.date_fin_three_t_two = False
                record.date_depart_four_t_two = False
                record.date_fin_four_t_two = False

            if len(tarifs) > 2:
                record.nbr_de_t_three = tarifs[2].nbr_de
                record.nbr_au_t_three = tarifs[2].nbr_au
                record.date_depart_one_t_three = tarifs[2].date_depart_one
                record.date_fin_one_t_three = tarifs[2].date_fin_one
                record.date_depart_two_t_three = tarifs[2].date_depart_two
                record.date_fin_two_t_three = tarifs[2].date_fin_two
                record.date_depart_three_t_three = tarifs[2].date_depart_three
                record.date_fin_three_t_three = tarifs[2].date_fin_three
                record.date_depart_four_t_three = tarifs[2].date_depart_four
                record.date_fin_four_t_three = tarifs[2].date_fin_four
            else:
                record.nbr_de_t_three = False
                record.nbr_au_t_three = False
                record.date_depart_one_t_three = False
                record.date_fin_one_t_three = False
                record.date_depart_two_t_three = False
                record.date_fin_two_t_three = False
                record.date_depart_three_t_three = False
                record.date_fin_three_t_three = False
                record.date_depart_four_t_three = False
                record.date_fin_four_t_three = False

            if len(tarifs) > 3:
                record.nbr_de_t_four = tarifs[3].nbr_de
                record.nbr_au_t_four = tarifs[3].nbr_au
                record.date_depart_one_t_four = tarifs[3].date_depart_one
                record.date_fin_one_t_four = tarifs[3].date_fin_one
                record.date_depart_two_t_four = tarifs[3].date_depart_two
                record.date_fin_two_t_four = tarifs[3].date_fin_two
                record.date_depart_three_t_four = tarifs[3].date_depart_three
                record.date_fin_three_t_four = tarifs[3].date_fin_three
                record.date_depart_four_t_four = tarifs[3].date_depart_four
                record.date_fin_four_t_four = tarifs[3].date_fin_four
            else:
                record.nbr_de_t_four = False
                record.nbr_au_t_four = False
                record.date_depart_one_t_four = False
                record.date_fin_one_t_four = False
                record.date_depart_two_t_four = False
                record.date_fin_two_t_four = False
                record.date_depart_three_t_four = False
                record.date_fin_three_t_four = False
                record.date_depart_four_t_four = False
                record.date_fin_four_t_four = False

            if len(tarifs) > 4:
                record.nbr_de_t_five = tarifs[4].nbr_de
                record.nbr_au_t_five = tarifs[4].nbr_au
                record.date_depart_one_t_five = tarifs[4].date_depart_one
                record.date_fin_one_t_five = tarifs[4].date_fin_one
                record.date_depart_two_t_five = tarifs[4].date_depart_two
                record.date_fin_two_t_five = tarifs[4].date_fin_two
                record.date_depart_three_t_five = tarifs[4].date_depart_three
                record.date_fin_three_t_five = tarifs[4].date_fin_three
                record.date_depart_four_t_five = tarifs[4].date_depart_four
                record.date_fin_four_t_five = tarifs[4].date_fin_four
            else:
                record.nbr_de_t_five = False
                record.nbr_au_t_five = False
                record.date_depart_one_t_five = False
                record.date_fin_one_t_five = False
                record.date_depart_two_t_five = False
                record.date_fin_two_t_five = False
                record.date_depart_three_t_five = False
                record.date_fin_three_t_five = False
                record.date_depart_four_t_five = False
                record.date_fin_four_t_five = False

            if len(tarifs) > 5:
                record.nbr_de_t_six = tarifs[5].nbr_de
                record.nbr_au_t_six = tarifs[5].nbr_au
                record.date_depart_one_t_six = tarifs[5].date_depart_one
                record.date_fin_one_t_six = tarifs[5].date_fin_one
                record.date_depart_two_t_six = tarifs[5].date_depart_two
                record.date_fin_two_t_six = tarifs[5].date_fin_two
                record.date_depart_three_t_six = tarifs[5].date_depart_three
                record.date_fin_three_t_six = tarifs[5].date_fin_three
                record.date_depart_four_t_six = tarifs[5].date_depart_four
                record.date_fin_four_t_six = tarifs[5].date_fin_four
            else:
                record.nbr_de_t_six = False
                record.nbr_au_t_six = False
                record.date_depart_one_t_six = False
                record.date_fin_one_t_six = False
                record.date_depart_two_t_six = False
                record.date_fin_two_t_six = False
                record.date_depart_three_t_six = False
                record.date_fin_three_t_six = False
                record.date_depart_four_t_six = False
                record.date_fin_four_t_six = False

            if len(tarifs) > 6:
                record.nbr_de_t_seven = tarifs[6].nbr_de
                record.nbr_au_t_seven = tarifs[6].nbr_au
                record.date_depart_one_t_seven = tarifs[6].date_depart_one
                record.date_fin_one_t_seven = tarifs[6].date_fin_one
                record.date_depart_two_t_seven = tarifs[6].date_depart_two
                record.date_fin_two_t_seven = tarifs[6].date_fin_two
                record.date_depart_three_t_seven = tarifs[6].date_depart_three
                record.date_fin_three_t_seven = tarifs[6].date_fin_three
                record.date_depart_four_t_seven = tarifs[6].date_depart_four
                record.date_fin_four_t_seven = tarifs[6].date_fin_four
            else:
                record.nbr_de_t_seven = False
                record.nbr_au_t_seven = False
                record.date_depart_one_t_seven = False
                record.date_fin_one_t_seven = False
                record.date_depart_two_t_seven = False
                record.date_fin_two_t_seven = False
                record.date_depart_three_t_seven = False
                record.date_fin_three_t_seven = False
                record.date_depart_four_t_seven = False
                record.date_fin_four_t_seven = False

            if len(tarifs) > 7:
                record.nbr_de_t_eight = tarifs[7].nbr_de
                record.nbr_au_t_eight = tarifs[7].nbr_au
                record.date_depart_one_t_eight = tarifs[7].date_depart_one
                record.date_fin_one_t_eight = tarifs[7].date_fin_one
                record.date_depart_two_t_eight = tarifs[7].date_depart_two
                record.date_fin_two_t_eight = tarifs[7].date_fin_two
                record.date_depart_three_t_eight = tarifs[7].date_depart_three
                record.date_fin_three_t_eight = tarifs[7].date_fin_three
                record.date_depart_four_t_eight = tarifs[7].date_depart_four
                record.date_fin_four_t_eight = tarifs[7].date_fin_four
            else:
                record.nbr_de_t_eight = False
                record.nbr_au_t_eight = False
                record.date_depart_one_t_eight = False
                record.date_fin_one_t_eight = False
                record.date_depart_two_t_eight = False
                record.date_fin_two_t_eight = False
                record.date_depart_three_t_eight = False
                record.date_fin_three_t_eight = False
                record.date_depart_four_t_eight = False
                record.date_fin_four_t_eight = False

            if len(tarifs) > 8:
                record.nbr_de_t_nine = tarifs[8].nbr_de
                record.nbr_au_t_nine = tarifs[8].nbr_au
                record.date_depart_one_t_nine = tarifs[8].date_depart_one
                record.date_fin_one_t_nine = tarifs[8].date_fin_one
                record.date_depart_two_t_nine = tarifs[8].date_depart_two
                record.date_fin_two_t_nine = tarifs[8].date_fin_two
                record.date_depart_three_t_nine = tarifs[8].date_depart_three
                record.date_fin_three_t_nine = tarifs[8].date_fin_three
                record.date_depart_four_t_nine = tarifs[8].date_depart_four
                record.date_fin_four_t_nine = tarifs[8].date_fin_four
            else:
                record.nbr_de_t_nine = False
                record.nbr_au_t_nine = False
                record.date_depart_one_t_nine = False
                record.date_fin_one_t_nine = False
                record.date_depart_two_t_nine = False
                record.date_fin_two_t_nine = False
                record.date_depart_three_t_nine = False
                record.date_fin_three_t_nine = False
                record.date_depart_four_t_nine = False
                record.date_fin_four_t_nine = False

            if len(tarifs) > 9:
                record.nbr_de_t_ten = tarifs[9].nbr_de
                record.nbr_au_t_ten = tarifs[9].nbr_au
                record.date_depart_one_t_ten = tarifs[9].date_depart_one
                record.date_fin_one_t_ten = tarifs[9].date_fin_one
                record.date_depart_two_t_ten = tarifs[9].date_depart_two
                record.date_fin_two_t_ten = tarifs[9].date_fin_two
                record.date_depart_three_t_ten = tarifs[9].date_depart_three
                record.date_fin_three_t_ten = tarifs[9].date_fin_three
                record.date_depart_four_t_ten = tarifs[9].date_depart_four
                record.date_fin_four_t_ten = tarifs[9].date_fin_four
            else:
                record.nbr_de_t_ten = False
                record.nbr_au_t_ten = False
                record.date_depart_one_t_ten = False
                record.date_fin_one_t_ten = False
                record.date_depart_two_t_ten = False
                record.date_fin_two_t_ten = False
                record.date_depart_three_t_ten = False
                record.date_fin_three_t_ten = False
                record.date_depart_four_t_ten = False
                record.date_fin_four_t_ten = False

    prix_one = fields.Integer(string='Prix One', compute='_compute_prix_one', store=True)
    prix_two = fields.Integer(string='Prix Two', compute='_compute_prix_two', store=True)
    prix_three = fields.Integer(string='Prix Three', compute='_compute_prix_three', store=True)
    prix_four = fields.Integer(string='Prix Four', compute='_compute_prix_four', store=True)
    prix_five = fields.Integer(string='Prix Five', compute='_compute_prix_five', store=True)
    prix_six = fields.Integer(string='Prix Six', compute='_compute_prix_six', store=True)
    prix_seven = fields.Integer(string='Prix Seven', compute='_compute_prix_seven', store=True)
    prix_eight = fields.Integer(string='Prix Eight', compute='_compute_prix_eight', store=True)
    prix_nine = fields.Integer(string='Prix Nine', compute='_compute_prix_nine', store=True)
    prix_ten = fields.Integer(string='Prix Ten', compute='_compute_prix_ten', store=True)

    @api.depends('tarifs', 'tarifs.date_fin_four', 'tarifs.date_depart_four', 'tarifs.date_fin_three',
                 'tarifs.date_depart_three', 'tarifs.date_fin_two', 'tarifs.date_depart_two', 'tarifs.date_fin_one',
                 'tarifs.date_depart_one', 'tarifs.nb_jour', 'tarifs.nbr_au', 'tarifs.nbr_de')
    def _compute_prix_one(self):
        for record in self:
            prix = False
            tarifs_sorted = record.tarifs.sorted(key=lambda r: r.create_date) if record.tarifs else False
            if tarifs_sorted and tarifs_sorted[0].create_date:
                prix = tarifs_sorted[0].prix
            record.prix_one = prix

    @api.depends('tarifs', 'tarifs.prix')
    def _compute_prix_two(self):
        for record in self:
            prix = False
            tarifs_sorted = record.tarifs.sorted(key=lambda r: r.create_date) if record.tarifs else False
            if tarifs_sorted and len(tarifs_sorted) > 1 and tarifs_sorted[1].create_date:
                prix = tarifs_sorted[1].prix
            record.prix_two = prix

    @api.depends('tarifs', 'tarifs.prix')
    def _compute_prix_three(self):
        for record in self:
            prix = False
            tarifs_sorted = record.tarifs.sorted(key=lambda r: r.create_date) if record.tarifs else False
            if tarifs_sorted and len(tarifs_sorted) > 2 and tarifs_sorted[2].create_date:
                prix = tarifs_sorted[2].prix
            record.prix_three = prix

    @api.depends('tarifs', 'tarifs.prix')
    def _compute_prix_four(self):
        for record in self:
            prix = False
            tarifs_sorted = record.tarifs.sorted(key=lambda r: r.create_date) if record.tarifs else False
            if tarifs_sorted and len(tarifs_sorted) > 3 and tarifs_sorted[3].create_date:
                prix = tarifs_sorted[3].prix
            record.prix_four = prix

    @api.depends('tarifs', 'tarifs.prix')
    def _compute_prix_five(self):
        for record in self:
            prix = False
            tarifs_sorted = record.tarifs.sorted(key=lambda r: r.create_date) if record.tarifs else False
            if tarifs_sorted and len(tarifs_sorted) > 4 and tarifs_sorted[4].create_date:
                prix = tarifs_sorted[4].prix
            record.prix_five = prix

    @api.depends('tarifs', 'tarifs.prix')
    def _compute_prix_six(self):
        for record in self:
            prix = False
            tarifs_sorted = record.tarifs.sorted(key=lambda r: r.create_date) if record.tarifs else False
            if tarifs_sorted and len(tarifs_sorted) > 5 and tarifs_sorted[5].create_date:
                prix = tarifs_sorted[5].prix
            record.prix_six = prix

    @api.depends('tarifs', 'tarifs.prix')
    def _compute_prix_seven(self):
        for record in self:
            prix = False
            tarifs_sorted = record.tarifs.sorted(key=lambda r: r.create_date) if record.tarifs else False
            if tarifs_sorted and len(tarifs_sorted) > 6 and tarifs_sorted[6].create_date:
                prix = tarifs_sorted[6].prix
            record.prix_seven = prix

    @api.depends('tarifs', 'tarifs.prix')
    def _compute_prix_eight(self):
        for record in self:
            prix = False
            tarifs_sorted = record.tarifs.sorted(key=lambda r: r.create_date) if record.tarifs else False
            if tarifs_sorted and len(tarifs_sorted) > 7 and tarifs_sorted[7].create_date:
                prix = tarifs_sorted[7].prix
            record.prix_eight = prix

    @api.depends('tarifs', 'tarifs.prix')
    def _compute_prix_nine(self):
        for record in self:
            prix = False
            tarifs_sorted = record.tarifs.sorted(key=lambda r: r.create_date) if record.tarifs else False
            if tarifs_sorted and len(tarifs_sorted) > 8 and tarifs_sorted[8].create_date:
                prix = tarifs_sorted[8].prix
            record.prix_nine = prix

    @api.depends('tarifs', 'tarifs.prix')
    def _compute_prix_ten(self):
        for record in self:
            prix = False
            tarifs_sorted = record.tarifs.sorted(key=lambda r: r.create_date) if record.tarifs else False
            if tarifs_sorted and len(tarifs_sorted) > 9 and tarifs_sorted[9].create_date:
                prix = tarifs_sorted[9].prix
            record.prix_ten = prix
