def migrate(cr, version):
    # 1. Obtener IDs de las acciones antiguas (por nombre)
    cr.execute("""
        SELECT id FROM ir_act_window 
        WHERE name->>'en_US' IN ('Precio Promedio (Prueba)', 'Porcentaje de Producción')
    """)
    action_ids = [row[0] for row in cr.fetchall()]
    
    if action_ids:
        # 2. Eliminar tarjetas que referencian esas acciones
        cr.execute("DELETE FROM dashboard_report WHERE action_id = ANY(%s)", (action_ids,))
        
        # 3. Eliminar los registros ir.model_data de esas acciones
        cr.execute("""
            DELETE FROM ir_model_data 
            WHERE module = 'balg_reportes_gerencia' 
              AND model = 'ir.actions.act_window' 
              AND name IN ('action_reporte_precio_promedio_prueba', 'action_reporte_produccion_porcentaje')
        """)
        
        # 4. Eliminar las acciones
        cr.execute("DELETE FROM ir_act_window WHERE id = ANY(%s)", (action_ids,))
    
    # 5. Eliminar ir.model_data de tarjetas antiguas (por si quedaron)
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE module = 'balg_reportes_gerencia' 
          AND model = 'dashboard.report' 
          AND name IN ('dashboard_report_precio_promedio_prueba', 'dashboard_report_produccion_porcentaje')
    """)