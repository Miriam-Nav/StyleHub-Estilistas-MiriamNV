from odoo import fields, models, api

class PeluqueriaEstilista(models.Model):
    _name = 'peluqueria.estilista'
    _description = 'Estilistas de la Peluquería'

    name = fields.Char(string='Nombre', required=True)
    activo = fields.Boolean(string='En Plantilla', default=True)
    
    # Campos nuevos útiles
    telefono = fields.Char(string='Teléfono')
    email = fields.Char(string='Email')
    foto = fields.Binary(string='Foto')
    notas = fields.Text(string='Notas')
    
    # Campo computado: contar cuántas citas tiene
    cita_ids = fields.One2many('peluqueria.cita', 'estilista_id', string='Citas')
    total_citas = fields.Integer(string='Total Citas', compute='_compute_total_citas', store=True)
    
    @api.depends('cita_ids')
    def _compute_total_citas(self):
        for estilista in self:
            estilista.total_citas = len(estilista.cita_ids)

    def action_ver_citas(self):
        return {
            'name': 'Citas de ' + self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'peluqueria.cita',
            'view_mode': 'list,form,calendar',
            'domain': [('estilista_id', '=', self.id)],
            'context': {'default_estilista_id': self.id}
        }