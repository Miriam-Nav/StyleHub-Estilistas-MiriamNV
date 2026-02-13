from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PeluqueriaCitaLinea(models.Model):
    _name = 'peluqueria.cita.linea'
    _description = 'Línea de Servicio de la Cita'

    _rec_name = 'servicio_id'

    # Una linea solo puede estar en una cita
    cita_id = fields.Many2one('peluqueria.cita', string='Cita', ondelete='cascade')
    
    # Un servicio solo puede estar en una linea
    servicio_id = fields.Many2one('peluqueria.servicio', string='Servicio', required=True)

    color = fields.Integer(string='Color', default=4)

    precio_unitario = fields.Float(string='Precio aplicado')
    duracion_servicio = fields.Float(string='Duración (h)')

    # Cuando el valor de servicio_id cambie se ejecuta esta función.
    @api.onchange('servicio_id')
    def _onchange_servicio_id(self):
        if self.servicio_id:
            # Trae el precio y la duración desde el modelo peluqueria.servicio
            self.precio_unitario = self.servicio_id.precio_base
            self.duracion_servicio = self.servicio_id.duracion
        else:
            self.precio_unitario = 0.0
            self.duracion_servicio = 0.0

    # Validar valores positivos (Precio)
    @api.constrains('precio_unitario')
    def _check_precio_positivo(self):
        for record in self:
            if record.precio_unitario < 0:
                raise ValidationError("El precio no puede ser negativo.")
            
    # Validar valores positivos (Duración)
    @api.constrains('duracion_servicio')
    def _check_duracion_positiva(self):
        for record in self:
            if record.duracion_servicio < 0:
                raise ValidationError("La duración no puede ser negativa.")

    # Validar servicio duplicado
    _sql_constraints = [
        ('unique_servicio_por_cita', 
         'unique(cita_id, servicio_id)', 
         'No puedes añadir el mismo servicio dos veces a la misma cita.')
    ]