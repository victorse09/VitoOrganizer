# =============================================================================
# Vito Organizer v2.2 - Agenda Renderer
# Motor de renderizado de páginas de agenda (página completa con estilos)
# Estilo visual: Lotus Organizer (libro abierto sobre escritorio)
# =============================================================================

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QFont
)
from PyQt6.QtWidgets import QWidget

from graphics.page_styles import PageStyles
from graphics.ring_binder import RingBinder
from graphics.textures import Textures


class AgendaRenderer:
    """Motor de renderizado que dibuja las páginas como agenda de papel.
    
    Estilo Lotus Organizer: libro abierto sobre un escritorio gris,
    con páginas de papel crema, agujeros de perforación prominentes
    y efecto de profundidad realista.
    """

    PAGE_CORNER_RADIUS = 3
    PAGE_MARGIN = 6

    @classmethod
    def draw_open_book(cls, painter: QPainter, rect: QRectF,
                       page_color: str = '#FFFDD0',
                       page_style: str = 'lined',
                       binding_type: str = 'rings',
                       ring_color: str = '#B0B0B0',
                       line_color: str = '#B0C4DE',
                       margin_color: str = '#E88888',
                       show_margin: bool = True,
                       line_spacing: int = 24,
                       left_page_num: int = 0,
                       right_page_num: int = 0):
        """Dibuja el libro abierto completo: dos páginas + encuadernación."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        binder_width = RingBinder.get_binder_width(binding_type)

        # Calcular rectángulos de las dos páginas
        available_width = rect.width() - binder_width - cls.PAGE_MARGIN * 2
        page_width = available_width / 2

        left_page_rect = QRectF(
            rect.left() + cls.PAGE_MARGIN,
            rect.top() + cls.PAGE_MARGIN,
            page_width,
            rect.height() - cls.PAGE_MARGIN * 2
        )

        right_page_rect = QRectF(
            rect.left() + cls.PAGE_MARGIN + page_width + binder_width,
            rect.top() + cls.PAGE_MARGIN,
            page_width,
            rect.height() - cls.PAGE_MARGIN * 2
        )

        binder_rect = QRectF(
            rect.left() + cls.PAGE_MARGIN + page_width,
            rect.top() + cls.PAGE_MARGIN,
            binder_width,
            rect.height() - cls.PAGE_MARGIN * 2
        )

        # Calcular rectángulo de la cubierta (más grande que las páginas)
        cover_rect = rect.adjusted(-20, -15, 20, 15)

        # Dibujar sombra del libro (sobre la cubierta)
        cls._draw_book_shadow(painter, cover_rect)

        # Dibujar cubierta de cuero (teal oscuro)
        painter.save()
        
        # Crear un path para los bordes redondeados
        from PyQt6.QtGui import QPainterPath
        cover_path = QPainterPath()
        cover_path.addRoundedRect(cover_rect, 8, 8)
        
        # Clip para la textura
        painter.setClipPath(cover_path)
        Textures.draw_sidebar_texture(painter, cover_rect, '#1a4742')
        painter.restore()

        # Dibujar bisel/borde 3D para darle grosor a la cubierta
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Borde exterior oscuro
        painter.setPen(QPen(QColor(0, 0, 0, 150), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(cover_rect, 8, 8)
        
        # Highlight interior arriba/izquierda
        inner_rect = cover_rect.adjusted(1.5, 1.5, -1.5, -1.5)
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1.5))
        painter.drawRoundedRect(inner_rect, 7, 7)
        painter.restore()

        # Dibujar página izquierda
        cls._draw_page(painter, left_page_rect, page_color, page_style,
                       line_color, margin_color, show_margin, line_spacing,
                       is_left=True, binding_type=binding_type, page_num=left_page_num)

        # Dibujar página derecha
        cls._draw_page(painter, right_page_rect, page_color, page_style,
                       line_color, margin_color, show_margin, line_spacing,
                       is_left=False, binding_type=binding_type, page_num=right_page_num)

        # Dibujar encuadernación
        RingBinder.draw(binding_type, painter, binder_rect, ring_color)

        # Sombras de profundidad en las páginas (más intensas)
        Textures.draw_page_shadow(painter, left_page_rect, 'right')
        Textures.draw_page_shadow(painter, right_page_rect, 'left')
        Textures.draw_page_shadow(painter, left_page_rect, 'bottom')
        Textures.draw_page_shadow(painter, right_page_rect, 'bottom')

        # Efecto de páginas apiladas (bloque de papel grueso hasta las pestañas)
        Textures.draw_page_edge(painter, right_page_rect, side='right', cover_rect=cover_rect)
        Textures.draw_page_edge(painter, left_page_rect, side='left', cover_rect=cover_rect)

        painter.restore()

    @classmethod
    def _draw_book_shadow(cls, painter: QPainter, rect: QRectF):
        """Dibuja la sombra exterior del libro (más prominente para look realista)."""
        # Sombra exterior difusa
        for i in range(6):
            shadow_offset = 3 + i
            alpha = 35 - i * 5
            if alpha <= 0:
                break
            shadow_rect = QRectF(
                rect.left() + shadow_offset + cls.PAGE_MARGIN,
                rect.top() + shadow_offset + cls.PAGE_MARGIN,
                rect.width() - cls.PAGE_MARGIN * 2,
                rect.height() - cls.PAGE_MARGIN * 2
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, alpha)))
            painter.drawRoundedRect(shadow_rect, 4, 4)

    @classmethod
    def _draw_page(cls, painter: QPainter, rect: QRectF,
                   page_color: str, page_style: str,
                   line_color: str, margin_color: str,
                   show_margin: bool, line_spacing: int,
                   is_left: bool = True, binding_type: str = 'rings',
                   page_num: int = 0):
        """Dibuja una página individual con su estilo."""
        # Fondo de la página (color crema/papel)
        bg_color = QColor(page_color)
        
        # Borde fino tipo papel
        painter.setPen(QPen(QColor('#B0A890'), 0.8))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, cls.PAGE_CORNER_RADIUS, cls.PAGE_CORNER_RADIUS)

        # Gradiente sutil para dar efecto de papel envejecido
        paper_grad = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
        paper_grad.setColorAt(0.0, QColor(255, 255, 240, 30))   # Ligeramente más claro arriba-izq
        paper_grad.setColorAt(0.3, QColor(0, 0, 0, 0))
        paper_grad.setColorAt(0.7, QColor(0, 0, 0, 5))
        paper_grad.setColorAt(1.0, QColor(180, 160, 120, 15))   # Ligeramente más oscuro abajo-der
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(paper_grad))
        painter.drawRoundedRect(rect, cls.PAGE_CORNER_RADIUS, cls.PAGE_CORNER_RADIUS)

        # Efecto de pliegue central (sombra vertical en el borde interno)
        if is_left:
            fold_rect = QRectF(rect.right() - 15, rect.top(), 15, rect.height())
            fold_grad = QLinearGradient(fold_rect.left(), 0, fold_rect.right(), 0)
            fold_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
            fold_grad.setColorAt(0.7, QColor(0, 0, 0, 10))
            fold_grad.setColorAt(1.0, QColor(0, 0, 0, 25))
        else:
            fold_rect = QRectF(rect.left(), rect.top(), 15, rect.height())
            fold_grad = QLinearGradient(fold_rect.left(), 0, fold_rect.right(), 0)
            fold_grad.setColorAt(0.0, QColor(0, 0, 0, 25))
            fold_grad.setColorAt(0.3, QColor(0, 0, 0, 10))
            fold_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(fold_grad))
        painter.drawRect(fold_rect)

        # Dibujar estilo de página (líneas, cuadrícula, etc.)
        style_kwargs = {
            'line_color': line_color,
            'margin_color': margin_color,
            'show_margin': show_margin and is_left,
            'line_spacing': line_spacing,
        }
        # Para cuadrícula y puntos, pasar parámetros adaptados
        if page_style == 'grid':
            style_kwargs = {'line_color': line_color, 'line_spacing': line_spacing // 1}
        elif page_style == 'dots':
            style_kwargs = {'dot_color': line_color, 'dot_spacing': line_spacing}

        PageStyles.draw(page_style, painter, rect, **style_kwargs)

        # Agujeros para la encuadernación (lado interno de la página)
        cls._draw_page_holes(painter, rect, is_left, binding_type)

        # Número diminuto de página en las esquinas inferiores
        if page_num > 0:
            painter.save()
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QColor('#777766'))
            num_str = str(page_num)
            if is_left:
                num_rect = QRectF(rect.left() + 14, rect.bottom() - 18, 40, 14)
                painter.drawText(num_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, num_str)
            else:
                num_rect = QRectF(rect.right() - 54, rect.bottom() - 18, 40, 14)
                painter.drawText(num_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, num_str)
            painter.restore()

    @classmethod
    def _draw_page_holes(cls, painter: QPainter, rect: QRectF, is_left: bool, binding_type: str):
        """Dibuja los agujeros de perforación en el borde interno de la página."""
        if binding_type not in ['rings', 'spiral']:
            return

        if binding_type == 'rings':
            num_holes = 7
            total_height = rect.height() - 80
            spacing = total_height / (num_holes + 1)
            hole_radius = 6
        elif binding_type == 'spiral':
            coil_height = 16
            num_holes = int((rect.height() - 60) / coil_height)
            spacing = coil_height
            hole_radius = 3.5

        for i in range(num_holes):
            if binding_type == 'rings':
                y = rect.top() + 40 + spacing * (i + 1)
            else:
                y = rect.top() + 30 + i * spacing + spacing / 2.0
                
            if is_left:
                x = rect.right() - hole_radius - 3
            else:
                x = rect.left() + 3

            cx = x + hole_radius
            cy = y

            # Sombra del agujero (efecto hundido)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 25)))
            painter.drawEllipse(int(cx - hole_radius + 1), int(cy - hole_radius + 1),
                                int(hole_radius * 2), int(hole_radius * 2))

            # Agujero principal (ligeramente grisáceo)
            hole_color = QColor('#D0CFC0')
            painter.setPen(QPen(QColor('#A0A090'), 0.6))
            painter.setBrush(QBrush(hole_color))
            painter.drawEllipse(int(cx - hole_radius), int(cy - hole_radius),
                                int(hole_radius * 2), int(hole_radius * 2))

            # Highlight interno (efecto 3D hundido)
            highlight_color = QColor(255, 255, 255, 50)
            painter.setPen(QPen(highlight_color, 0.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(int(cx - hole_radius + 1), int(cy - hole_radius + 1),
                           int((hole_radius - 1) * 2), int((hole_radius - 1) * 2),
                           30 * 16, 120 * 16)

    @classmethod
    def get_page_content_rect(cls, rect: QRectF, binding_type: str = 'rings',
                              is_left: bool = True) -> QRectF:
        """Retorna el rectángulo utilizable para contenido dentro de una página."""
        binder_width = RingBinder.get_binder_width(binding_type)
        available_width = rect.width() - binder_width - cls.PAGE_MARGIN * 2
        page_width = available_width / 2

        content_margin = 20  # Margen interno del contenido
        hole_margin = 18     # Margen para los agujeros (un poco más por agujeros más grandes)

        if is_left:
            page_rect = QRectF(
                rect.left() + cls.PAGE_MARGIN + content_margin,
                rect.top() + cls.PAGE_MARGIN + content_margin,
                page_width - content_margin - hole_margin,
                rect.height() - cls.PAGE_MARGIN * 2 - content_margin * 2
            )
        else:
            page_rect = QRectF(
                rect.left() + cls.PAGE_MARGIN + page_width + binder_width + hole_margin,
                rect.top() + cls.PAGE_MARGIN + content_margin,
                page_width - content_margin - hole_margin,
                rect.height() - cls.PAGE_MARGIN * 2 - content_margin * 2
            )

        return page_rect

    @classmethod
    def draw_single_page(cls, painter: QPainter, rect: QRectF,
                         page_color: str = '#FFFDD0',
                         page_style: str = 'lined',
                         line_color: str = '#B0C4DE',
                         margin_color: str = '#E88888',
                         show_margin: bool = False,
                         line_spacing: int = 24):
        """Dibuja una página única sin encuadernación que ocupa todo el ancho.

        Modo especial para vistas panorámicas tipo Lotus Organizer:
        una sola hoja sobre el escritorio, sin cubierta de cuero,
        sin encuadernación y sin agujeros de perforación.
        """
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Rectángulo de la página única (todo el ancho con márgenes)
        page_rect = QRectF(
            rect.left() + cls.PAGE_MARGIN,
            rect.top() + cls.PAGE_MARGIN,
            rect.width() - cls.PAGE_MARGIN * 2,
            rect.height() - cls.PAGE_MARGIN * 2
        )

        # Calcular rectángulo de la cubierta (más grande que la página)
        cover_rect = rect.adjusted(-20, -15, 20, 15)

        # Dibujar sombra del libro
        cls._draw_book_shadow(painter, cover_rect)

        # Dibujar cubierta de cuero (teal oscuro)
        from PyQt6.QtGui import QPainterPath
        cover_path = QPainterPath()
        cover_path.addRoundedRect(cover_rect, 8, 8)

        painter.save()
        painter.setClipPath(cover_path)
        Textures.draw_sidebar_texture(painter, cover_rect, '#1a4742')
        painter.restore()

        # Borde 3D de la cubierta
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(0, 0, 0, 150), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(cover_rect, 8, 8)
        inner_rect = cover_rect.adjusted(1.5, 1.5, -1.5, -1.5)
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1.5))
        painter.drawRoundedRect(inner_rect, 7, 7)
        painter.restore()

        # Dibujar la página única (sin agujeros, sin fold, sin page_num)
        bg_color = QColor(page_color)
        painter.setPen(QPen(QColor('#B0A890'), 0.8))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(page_rect, cls.PAGE_CORNER_RADIUS, cls.PAGE_CORNER_RADIUS)

        # Gradiente sutil de papel envejecido
        paper_grad = QLinearGradient(page_rect.left(), page_rect.top(), page_rect.right(), page_rect.bottom())
        paper_grad.setColorAt(0.0, QColor(255, 255, 240, 30))
        paper_grad.setColorAt(0.3, QColor(0, 0, 0, 0))
        paper_grad.setColorAt(0.7, QColor(0, 0, 0, 5))
        paper_grad.setColorAt(1.0, QColor(180, 160, 120, 15))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(paper_grad))
        painter.drawRoundedRect(page_rect, cls.PAGE_CORNER_RADIUS, cls.PAGE_CORNER_RADIUS)

        # Estilo de página (líneas, cuadrícula, etc.)
        style_kwargs = {
            'line_color': line_color,
            'margin_color': margin_color,
            'show_margin': show_margin,
            'line_spacing': line_spacing,
        }
        if page_style == 'grid':
            style_kwargs = {'line_color': line_color, 'line_spacing': line_spacing // 1}
        elif page_style == 'dots':
            style_kwargs = {'dot_color': line_color, 'dot_spacing': line_spacing}

        PageStyles.draw(page_style, painter, page_rect, **style_kwargs)

        # Sombras de profundidad en todos los bordes
        Textures.draw_page_shadow(painter, page_rect, 'right')
        Textures.draw_page_shadow(painter, page_rect, 'left')
        Textures.draw_page_shadow(painter, page_rect, 'bottom')

        # Bordes de páginas apiladas
        Textures.draw_page_edge(painter, page_rect, side='right', cover_rect=cover_rect)
        Textures.draw_page_edge(painter, page_rect, side='left', cover_rect=cover_rect)

        painter.restore()

