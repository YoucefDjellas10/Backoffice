from odoo import models, fields, api
from odoo.exceptions import UserError
import random
import string


class ListeClient(models.Model):
    _name = 'liste.client'
    _description = 'liste des clients'

    name = fields.Char(string='Nom complet', compute='_compute_full_name', store=True)
    civilite = fields.Selection([('Mr', 'M.'), ('Mme', 'Mme'), ('Mlle', 'Mlle')], string='Civilité')
    nom = fields.Char(string='Nom', required=True)
    prenom = fields.Char(string='Prénom')
    email = fields.Char(string='Email')
    date_de_naissance = fields.Date(string='Date de naissance')
    mobile = fields.Char(string='Mobile')
    telephone = fields.Char(string='Téléphone')
    risque = fields.Selection([('faible', 'Faible'), ('moyen', 'Moyen'), ('eleve', 'Elevé')], string='Risque',
                              default='faible')
    note = fields.Text(string='Note')
    date_de_permis = fields.Date(string='Date de permis')
    categorie_client = fields.Many2one('categorie.client', string='Categorie',
                                       compute='_compute_categorie_client', store=True)
    category_client_name = fields.Char(string='Category name',related='categorie_client.name', store=True)
    options_gratuit = fields.Many2many('options', string='Options Gratuites',
                                       related='categorie_client.options_gratuit')
    reduction = fields.Integer(string='Réduction %', related='categorie_client.reduction', store=True)

    total_points = fields.Integer(string='Total des points', compute='_compute_total_points', store=True, editable=True)
    total_points_char = fields.Char(string='Total des points', compute='_compute_total_points_char', store=True)
    solde = fields.Monetary(string='Solde non consomé', currency_field='devise', compute='_compute_solde', store=True, editable=True)
    devise = fields.Many2one('res.currency', string='Devise', readonly=True,
                             default=lambda self: self.env.ref('base.EUR').id)
    total_reservation = fields.Monetary(currency_field='devise')
    code_prime = fields.Char(string='Code Prime', store=True, readonly=True)

    parrain = fields.Many2one('liste.client', string='Le parrain')
    filleul = fields.One2many('liste.client', 'parrain', string='Les filleuls')

    solde_total = fields.Integer(string='Solde Total')
    solde_consomer = fields.Integer(string='Solde consomé')

    otp = fields.Char(string='otp')
    otp_created_at = fields.Datetime(string='otp created at')
    otp_attempts = fields.Integer(string='opt attempts', default=0)


    create_date = fields.Datetime()

    @api.depends('solde_total', 'solde_consomer')
    def _compute_solde(self):
        for record in self:
            record.solde = record.solde_total - record.solde_consomer if record.solde_total else 0

    def action_ajouter_filleul_direct(self):
        return {
            'name': 'Ajouter un Filleul',
            'type': 'ir.actions.act_window',
            'res_model': 'liste.client',
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('liste_clients.view_filleul_form_popup').id,
            'context': {'default_parrain': self.id},
        }

    def action_save(self):
        solde_parrainage_record = self.env['solde.parrainage'].search([], limit=1)
        if not solde_parrainage_record:
            raise UserError("Aucun enregistrement trouvé dans Solde Parrainage.")
        self.solde_total += solde_parrainage_record.parrain_solde
        new_filleul_id = self.env.context.get('active_id')
        new_filleul = self.env['liste.client'].browse(new_filleul_id)
        if not new_filleul:
            raise UserError("Aucun enregistrement filleul n'a été trouvé.")
        new_filleul.solde_total += solde_parrainage_record.filleul_solde
        return {'type': 'ir.actions.act_window_close'}

    @api.depends('total_points')
    def _compute_categorie_client(self):
        for record in self:
            categorie = self.env['categorie.client'].search([
                ('du_pts', '<=', record.total_points),
                ('au_pts', '>=', record.total_points)
            ], limit=1)

            record.categorie_client = categorie.id if categorie else False

    @api.depends('total_reservation')
    def _compute_total_points(self):
        for record in self:
            record.total_points = int(record.total_reservation)

    @api.depends('civilite', 'nom', 'prenom')
    def _compute_full_name(self):
        for record in self:
            # Concatenate civilite, nom, and prenom with spaces
            record.name = ' '.join(filter(None, [record.civilite, record.nom, record.prenom]))

    def action_send_welcome_email(self):
        template_id = self.env.ref('liste_clients.email_template_welcome_client').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def action_enregistrement_email(self):
        template_id = self.env.ref('liste_clients.template_enregistrement_compte_client').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def action_newslatter_email(self):
        template_id = self.env.ref('liste_clients.template_newslatter_client').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def action_driver_email(self):
        template_id = self.env.ref('liste_clients.template_driver_client_finale_template_').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    @api.depends('total_points')
    def _compute_total_points_char(self):
        for record in self:
            record.total_points_char = f"{record.total_points} pts"
