import os
import re
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

BASE_IMG_DIR = '/home/odoo/data/balgres_web'
FILENAME_RE = re.compile(r'^baldosa_(.+?)_(\d+x\d+)$')
FORMATOS_VALIDOS = {'20x20', '27x36', '36x36', '36x48', '36x72', '48x48'}


class BalgresProduct(models.Model):
    _name = 'balgres.product'
    _description = 'Catálogo Web Balgres'
    _order = 'formato, sequence, name'

    name = fields.Char(required=True)
    slug = fields.Char(required=True, index=True)
    formato = fields.Selection(
        [(f, f.replace('x', ' x ')) for f in FORMATOS_VALIDOS],
        required=True,
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    image_base_path  = fields.Char()
    image_hover_path = fields.Char()

    image_base_url  = fields.Char(compute='_compute_image_urls')
    image_hover_url = fields.Char(compute='_compute_image_urls')

    @api.depends('image_base_path', 'image_hover_path')
    def _compute_image_urls(self):
        for rec in self:
            rec.image_base_url = self._build_url(rec.image_base_path)
            rec.image_hover_url = self._build_url(rec.image_hover_path)

    @api.model
    def _build_url(self, relpath):
        """Construye la URL con cache-busting usando mtime del archivo."""
        if not relpath:
            return ''
        full = os.path.join(BASE_IMG_DIR, relpath)
        try:
            mtime = int(os.path.getmtime(full))
        except OSError:
            mtime = 0
        return f'/balgres_imagen/{relpath}?v={mtime}'

    @api.model
    def sync_from_folder(self):
        if not os.path.isdir(BASE_IMG_DIR):
            _logger.warning("[Balgres] No existe %s", BASE_IMG_DIR)
            return

        encontrados = {}
        skipped = 0

        for formato in sorted(os.listdir(BASE_IMG_DIR)):
            if formato not in FORMATOS_VALIDOS:
                continue

            imagen_dir = os.path.join(BASE_IMG_DIR, formato, 'imagen')
            render_dir = os.path.join(BASE_IMG_DIR, formato, 'render')

            if not os.path.isdir(imagen_dir):
                continue

            for filename in sorted(os.listdir(imagen_dir)):
                if not filename.lower().endswith(('.webp', '.jpg', '.jpeg', '.png')):
                    continue

                stem = os.path.splitext(filename)[0]
                match = FILENAME_RE.match(stem)
                if not match:
                    _logger.warning("[Balgres] Nombre inválido: %s", filename)
                    skipped += 1
                    continue

                descripcion, fmt_from_name = match.groups()
                if fmt_from_name != formato:
                    _logger.warning(
                        "[Balgres] Formato carpeta (%s) ≠ archivo (%s)",
                        formato, filename,
                    )
                    skipped += 1
                    continue

                slug = f'{descripcion}_{formato}'

                hover_path = ''
                if os.path.isdir(render_dir):
                    render_stem = f'render_{slug}'
                    for ext in ('.webp', '.jpg', '.jpeg', '.png'):
                        candidate = os.path.join(render_dir, render_stem + ext)
                        if os.path.isfile(candidate):
                            hover_path = f'{formato}/render/{render_stem}{ext}'
                            break

                encontrados[slug] = {
                    'name': descripcion.replace('_', ' ').title(),
                    'formato': formato,
                    'image_base_path': f'{formato}/imagen/{filename}',
                    'image_hover_path': hover_path,
                }

        _logger.info("[Balgres] En disco: %d productos", len(encontrados))

        existentes = self.search([])
        slugs_bd = set(existentes.mapped('slug'))
        slugs_disco = set(encontrados.keys())

        huerfanos = slugs_bd - slugs_disco
        if huerfanos:
            existentes.filtered(lambda p: p.slug in huerfanos).unlink()

        created = updated = 0
        for slug, data in encontrados.items():
            existing = self.search([('slug', '=', slug)], limit=1)
            if existing:
                vals = {f: v for f, v in data.items() if getattr(existing, f) != v}
                if vals:
                    existing.write(vals)
                    updated += 1
            else:
                self.create({'slug': slug, **data})
                created += 1

        _logger.info(
            "[Balgres] Sync → %d creados, %d actualizados, %d borrados, %d omitidos",
            created, updated, len(huerfanos), skipped,
        )