"""
Generador de calendarios HTML con festivos destacados
"""

from datetime import datetime, timedelta
from typing import List, Dict
import calendar


class CalendarGenerator:
    """Genera calendarios HTML visualmente atractivos"""
    
    # Meses en español
    MESES = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    
    # Días de la semana en español
    DIAS_SEMANA = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
    
    def __init__(self, year: int, festivos: List[Dict], municipio: str = "", ccaa: str = "", 
                 empresa: str = "", horario: Dict = None, datos_opcionales: Dict = None):
        self.year = year
        self.festivos = festivos
        self.municipio = municipio
        self.ccaa = ccaa
        self.empresa = empresa
        self.horario = horario or {}
        self.datos_opcionales = datos_opcionales or {}
        
        # Logo Biplaza embebido (base64)
        self.logo_base64 = self._get_logo_biplaza()
        
        # Convertir festivos a set para búsqueda rápida
        self.festivos_set = {f['fecha'] for f in festivos}
        
        # Diccionario fecha → festivo para tooltips
        self.festivos_dict = {f['fecha']: f for f in festivos}
    
    def _get_logo_biplaza(self) -> str:
        """Lee y convierte el logo de Biplaza a base64"""
        import base64
        import os
        
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'logo_320x132.gif')
        
        try:
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                return base64.b64encode(logo_data).decode()
        except FileNotFoundError:
            # Si no encuentra el logo, devolver string vacío
            return ""
    
    def generate_html(self) -> str:
        """Genera el HTML completo del calendario"""
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calendario Laboral {self.year}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    {self._get_header()}
    {self._get_calendar_grid()}
    {self._get_footer()}
</body>
</html>
"""
        return html
    
    def _get_css(self) -> str:
        """CSS del calendario"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        @page {
            size: A4;
            margin: 15mm;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            background: white;
            padding: 0;
            margin: 0;
        }
        
        .container {
            max-width: 210mm;
            margin: 0 auto;
            background: white;
            padding: 5mm;
        }
        
        /* === HEADER === */
        .header {
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 2px solid #F1AB6C;
            display: grid;
            grid-template-columns: 160px 1fr;
            align-items: flex-start;
            gap: 15px;
        }
        
        .header-left {
            text-align: left;
        }
        
        .header-right {
            text-align: right;
        }
        
        .header-left {
            text-align: left;
        }
        
        .header-center {
            text-align: center;
        }
        
        .header-right {
            text-align: right;
        }
        
        .logo {
            width: 160px;
            height: auto;
        }
        
        .header h1 {
            color: #333;
            font-size: 1.4em;
            margin: 0;
            font-weight: normal;
        }
        
        .header h2 {
            color: #333;
            font-size: 2em;
            font-weight: bold;
            margin: 0;
        }
        
        /* === CALENDARIO === */
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 6px;
            margin: 8px 0;
        }
        
        .month {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 3px;
            overflow: hidden;
        }
        
        .month-header {
            background: #F1AB6C;
            color: white;
            padding: 4px;
            font-weight: bold;
            text-align: center;
            font-size: 0.8em;
        }
        
        .weekdays {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            background: #f8f8f8;
            border-bottom: 1px solid #ddd;
        }
        
        .weekday {
            padding: 3px 2px;
            text-align: center;
            font-weight: bold;
            font-size: 0.65em;
            color: #666;
        }
        
        .days {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
        }
        
        .day {
            padding: 4px 2px;
            text-align: center;
            font-size: 0.7em;
            min-height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        
        .day.empty {
            background: #fafafa;
        }
        
        /* Sábados y domingos en gris */
        .day.sabado,
        .day.domingo {
            background: #e8e8e8;
        }
        
        /* Festivos nacionales/autonómicos */
        .day.festivo {
            background: #F1AB6C !important;
            color: white;
            font-weight: bold;
        }
        
        /* Festivos locales - con borde distintivo */
        .day.festivo.local {
            background: #F1AB6C !important;
            border: 2px solid #d4894a;
            box-shadow: inset 0 0 0 1px white;
        }
        
        .day.festivo:hover {
            opacity: 0.9;
        }
        
        /* === FOOTER === */
        .footer-content {
            margin-top: 12px;
            padding-top: 10px;
            border-top: 2px solid #eee;
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 15px;
            font-size: 0.85em;
        }
        
        /* Columna izquierda: Listado festivos */
        .festivos-list {
            padding-right: 15px;
            border-right: 1px solid #ddd;
        }
        
        .festivos-list h3 {
            font-size: 0.9em;
            color: #333;
            margin-bottom: 6px;
            font-weight: bold;
        }
        
        .festivo-item-list {
            margin: 3px 0;
            font-size: 0.75em;
            color: #555;
            line-height: 1.2;
        }
        
        .festivo-item-list.local {
            color: #F1AB6C;
            font-weight: bold;
        }
        
        /* Columna derecha: Info empresa */
        .info-empresa-footer {
            padding-left: 15px;
        }
        
        .info-empresa-footer .empresa-nombre-footer {
            font-size: 1.3em;
            color: #F1AB6C;
            font-weight: bold;
            margin-bottom: 12px;
        }
        
        .info-empresa-footer p {
            margin: 6px 0;
            font-size: 0.9em;
            color: #333;
            line-height: 1.5;
        }
        
        .info-empresa-footer .horario-box {
            margin: 12px 0;
            padding: 12px;
            background: #f8f8f8;
            border-left: 3px solid #F1AB6C;
            border-radius: 3px;
        }
        
        .info-empresa-footer .horario-box h4 {
            font-size: 0.95em;
            color: #333;
            margin-bottom: 8px;
        }
        
        .info-empresa-footer .horario-box p {
            margin: 4px 0;
            font-size: 0.85em;
        }
        
        .footer-meta {
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid #eee;
            text-align: center;
            font-size: 0.75em;
            color: #999;
        }
        
        @media print {
            body {
                background: white;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            
            .container {
                padding: 0;
                max-width: 100%;
            }
            
            * {
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            
            @page {
                size: A4;
                margin: 12mm;
            }
            
            .header {
                margin-bottom: 6px;
                padding-bottom: 6px;
            }
            
            .calendar-grid {
                gap: 4px;
                margin: 6px 0;
            }
            
            .footer-content {
                margin-top: 8px;
                padding-top: 8px;
                font-size: 0.8em;
            }
            
            .footer-meta {
                font-size: 0.65em;
            }
        }
        """
    
    def _get_header(self) -> str:
        """Genera el header del calendario con logo Biplaza, título y año alineados a la derecha"""
        
        logo_html = ""
        if self.logo_base64:
            logo_html = f'<img src="data:image/gif;base64,{self.logo_base64}" class="logo" alt="Biplaza">'
        
        return f"""
    <div class="container">
        <div class="header">
            <div class="header-left">
                {logo_html}
            </div>
            <div class="header-right">
                <h1>Calendario laboral</h1>
                <h2>{self.year}</h2>
            </div>
        </div>
"""
    
    def _get_calendar_grid(self) -> str:
        """Genera la cuadrícula de meses"""
        
        html = '<div class="calendar-grid">\n'
        
        for month in range(1, 13):
            html += self._generate_month(month)
        
        html += '</div>\n'
        return html
    
    def _generate_month(self, month: int) -> str:
        """Genera el HTML de un mes"""
        
        # Obtener información del mes
        month_name = self.MESES[month - 1]
        cal = calendar.monthcalendar(self.year, month)
        
        html = f"""
        <div class="month">
            <div class="month-header">{month_name}</div>
            <div class="weekdays">
"""
        
        # Días de la semana
        for day_name in self.DIAS_SEMANA:
            html += f'                <div class="weekday">{day_name}</div>\n'
        
        html += '            </div>\n            <div class="days">\n'
        
        # Días del mes
        for week in cal:
            for day_index, day in enumerate(week):
                if day == 0:
                    # Día vacío
                    html += '                <div class="day empty"></div>\n'
                else:
                    # Construir fecha
                    fecha = f"{self.year:04d}-{month:02d}-{day:02d}"
                    
                    # Determinar día de la semana (0=Lunes, 6=Domingo)
                    dia_semana = day_index
                    
                    # Clases CSS
                    clases = ['day']
                    
                    # Añadir clase de fin de semana (si no es festivo)
                    if fecha not in self.festivos_set:
                        if dia_semana == 5:  # Sábado
                            clases.append('sabado')
                        elif dia_semana == 6:  # Domingo
                            clases.append('domingo')
                    
                    # Verificar si es festivo (prioridad sobre fin de semana)
                    if fecha in self.festivos_set:
                        clases.append('festivo')
                        festivo = self.festivos_dict[fecha]
                        descripcion = festivo.get('descripcion', 'Festivo')
                        
                        # Añadir clase 'local' si es festivo local
                        if festivo.get('ambito') == 'municipal' or festivo.get('tipo') == 'local':
                            clases.append('local')
                        
                        html += f'                <div class="{" ".join(clases)}" data-festivo="{descripcion}">{day}</div>\n'
                    else:
                        html += f'                <div class="{" ".join(clases)}">{day}</div>\n'
        
        html += '            </div>\n        </div>\n'
        return html
    
    def _get_footer(self) -> str:
        """Genera el footer con listado festivos (izq) e info empresa (der)"""
        from datetime import datetime
        
        # === LISTADO DE FESTIVOS (todos, ordenados por fecha) ===
        festivos_ordenados = sorted(self.festivos, key=lambda x: x['fecha'])
        
        festivos_list_html = ""
        for fest in festivos_ordenados:
            fecha_obj = datetime.strptime(fest['fecha'], '%Y-%m-%d')
            dia = fecha_obj.day
            mes = self._get_month_name(fecha_obj.month)
            descripcion = fest.get('descripcion', '').replace('Ãrsula', 'Úrsula').replace('Ã', 'í')
            
            # Marcar locales con clase especial
            clase_extra = ' local' if fest.get('ambito') == 'municipal' or fest.get('tipo') == 'local' else ''
            
            festivos_list_html += f'<div class="festivo-item-list{clase_extra}">{dia} de {mes}: {descripcion}</div>\n'
        
        # === INFORMACIÓN EMPRESA ===
        empresa_html = f'<div class="empresa-nombre-footer">{self.empresa}</div>' if self.empresa else ''
        
        # Datos opcionales
        datos_html = ""
        if self.datos_opcionales.get('direccion'):
            direccion = self.datos_opcionales['direccion'].replace('\n', '<br>')
            datos_html += f'<p><strong>Domicilio del centro de trabajo:</strong><br>{direccion}</p>\n'
        
        if self.datos_opcionales.get('convenio'):
            datos_html += f'<p><strong>Convenio aplicable:</strong> {self.datos_opcionales["convenio"]}</p>\n'
        
        if self.datos_opcionales.get('num_patronal'):
            datos_html += f'<p><strong>Número patronal:</strong> {self.datos_opcionales["num_patronal"]}</p>\n'
        
        if self.datos_opcionales.get('mutua'):
            datos_html += f'<p><strong>Mutua de accidentes:</strong> {self.datos_opcionales["mutua"]}</p>\n'
        
        # === HORARIO ===
        horario_html = ""
        if self.horario.get('invierno'):
            if self.horario.get('tiene_verano') and self.horario.get('verano'):
                # Horario diferenciado
                horario_content = f"""
                    <p><strong>Horario invierno:</strong><br>{self.horario['invierno'].replace(chr(10), '<br>')}</p>
                    <p><strong>Horario verano:</strong><br>{self.horario['verano'].replace(chr(10), '<br>')}</p>
                """
                if self.horario.get('verano_inicio') and self.horario.get('verano_fin'):
                    inicio = self.horario['verano_inicio'].strftime('%d/%m')
                    fin = self.horario['verano_fin'].strftime('%d/%m')
                    horario_content += f"<p style='font-size: 0.8em; color: #666;'>(Del {inicio} al {fin})</p>"
                
                horario_html = f"""
                <div class="horario-box">
                    <h4>Horario laboral</h4>
                    {horario_content}
                </div>
                """
            else:
                # Horario único
                horario_html = f"""
                <div class="horario-box">
                    <h4>Horario laboral</h4>
                    <p>{self.horario['invierno'].replace(chr(10), '<br>')}</p>
                </div>
                """
        
        return f"""
        <div class="footer-content">
            <div class="festivos-list">
                <h3>FIESTAS LABORALES {self.year}</h3>
                {festivos_list_html}
            </div>
            
            <div class="info-empresa-footer">
                {empresa_html}
                {datos_html}
                {horario_html}
            </div>
        </div>
        
        <div class="footer-meta">
            <p>Municipio: {self.municipio.upper()}, {self.ccaa.upper()} | 
            Total festivos: {len(self.festivos)} | 
            Generado el {datetime.now().strftime('%d/%m/%Y')}</p>
        </div>
    </div>
"""
    
    def _get_month_name(self, month: int) -> str:
        """Devuelve nombre del mes en español"""
        meses = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        return meses.get(month, '')