# 📊 Reporte 6: Análisis de Separabilidad de Gestos y Plan de Mejora

**Fecha:** 28 de enero de 2026  
**Objetivo:** Mejorar la separación entre clases para alcanzar >85% accuracy  
**Estado actual:** ~67% accuracy con sobreposición significativa entre gestos

---

## 🔍 1. Análisis de Datos Actuales

### 1.1 Observaciones de las Gráficas

#### **Canal CH3 (Más Discriminativo)**

- ✅ **LEFT:** Separación positiva clara (rango 50-150)
- ⚠️ **RIGHT:** Tendencia negativa moderada (rango -50 a 0)
- ❌ **REST/UP:** Sobreposición severa (ambos centrados en 0±10)
- **Conclusión:** CH3 es nuestro canal principal pero insuficiente

#### **Canales CH1 y CH2 (Poco Discriminativos)**

- ❌ Sobreposición casi completa entre todas las clases
- ❌ Histogramas muestran densidad concentrada en 0±20
- ❌ Boxplots revelan IQR similares para todos los gestos
- **Conclusión:** No aportan información discriminativa en estado actual

#### **Outliers y Ruido**

- ⚠️ Valores extremos: ±200 (fuera del rango esperado)
- ⚠️ Outliers representan ~5-10% de datos
- ✅ Clipping P5-P95 implementado es efectivo
- **Origen probable:** Movimientos de cabeza, artefactos EMG

### 1.2 Métricas de Separabilidad Actual

| Clase | CH3 Mediana | Rango IQR | Separación vs REST |
| ----- | ----------- | --------- | ------------------ |
| REST  | ~0          | -10 a +10 | 0 (baseline)       |
| UP    | ~0          | -10 a +10 | **~0** ❌          |
| LEFT  | ~30         | 10 a 80   | **~30** ⚡         |
| RIGHT | ~-10        | -30 a 10  | **~10** ❌         |

**🎯 Meta:** Separación >60 para cada gesto (actualmente solo LEFT cercano)

---

## ⚠️ 2. Problemas Identificados

### 2.1 Sobreposición de Clases (Crítico)

```
Sobreposición actual en histogramas:
- REST vs UP:    >80% sobreposición ← Crítico
- REST vs RIGHT: >60% sobreposición ← Problema
- REST vs LEFT:  ~40% sobreposición ← Moderado
```

**Impacto:** El modelo no puede diferenciar gestos con señales tan similares

### 2.2 Baseline Inestable

- Drift temporal visible en gráficas de tiempo
- REST no permanece consistente en 0
- **Causa:** Calibración única al inicio, no se adapta

### 2.3 Canales Subutilizados

- CH1 y CH2 prácticamente no aportan información
- **Posible causa:** Gestos actuales no activan suficientes grupos musculares

### 2.4 Transiciones Contaminadas

- Ventanas incluyen muestras de transición gesto→REST
- Ventanas mixtas reducen pureza de datos de entrenamiento

---

## 🎯 3. Plan de Acción

### **Prioridad 1: Mejorar Recolección de Datos**

#### **Tarea 1.1: Rediseñar Protocolo de Gestos**

**Responsable:** Equipo de adquisición  
**Plazo:** 1 semana

**Acciones específicas:**

1. **Aumentar duración de fases:**
   - Actual: 1.5s gesto + 1.5s REST
   - **Nueva:** 2.0s gesto + 2.0s REST
   - **Razón:** Reducir contaminación por transiciones

2. **Incrementar intensidad de gestos:**
   - LEFT: Levantar ambas cejas **al máximo** (objetivo ch3 >100)
   - RIGHT: Levantar ceja derecha + apretar dientes lado derecho
   - UP: Levantar cejas + fruncir frente (activar CH2)
   - **Meta:** Separación CH3 >60 respecto a baseline

3. **Calibración por sesión:**
   - Recolectar 3-5s REST **antes de cada gesto**
   - Calcular baseline local (no global)
   - Aplicar corrección de drift en post-procesamiento

**Entregable:** Nuevo script de adquisición con timing 2s/2s

---

#### **Tarea 1.2: Activar Canales CH1 y CH2**

**Responsable:** Equipo de validación fisiológica  
**Plazo:** 1 semana

**Experimento propuesto:**

```
Probar variaciones de gestos que activen diferentes músculos:

Opción A (actual):
- LEFT:  Solo cejas arriba
- RIGHT: Solo ceja derecha
- UP:    Cejas arriba fuerte

Opción B (propuesta):
- LEFT:  Cejas arriba + sonrisa lado izquierdo
- RIGHT: Cejas arriba + sonrisa lado derecho
- UP:    Cejas + arrugar nariz

Opción C (propuesta):
- LEFT:  Cejas + morder lado izquierdo
- RIGHT: Cejas + morder lado derecho
- UP:    Cejas + apretar mandíbula
```

**Entregable:** Reporte con gráficas comparativas de 3 opciones (20 trials c/u)

---

### **Prioridad 2: Mejorar Procesamiento de Datos**

#### **Tarea 2.1: Implementar Filtro de Transiciones**

**Responsable:** Equipo de ML  
**Plazo:** 3 días

**Implementación en `model.py`:**

```python
def filter_transition_windows(window_df):
    """
    Rechaza ventanas con gradientes altos (transiciones).
    """
    for ch in ['ch1', 'ch2', 'ch3']:
        gradient = np.abs(np.diff(window_df[ch].values))
        if np.max(gradient) > 50:  # Umbral ajustable
            return False
    return True

# Agregar al loop de create_windows_multiclass():
if not filter_transition_windows(window):
    rejected_stats['high_gradient'] += 1
    continue
```

**Entregable:** PR con implementación + métricas de ventanas rechazadas

---

#### **Tarea 2.2: Agregar Métricas de Calidad de Datos**

**Responsable:** Equipo de ML  
**Plazo:** 2 días

**Implementación:**

```python
def evaluate_data_quality(df, output_path="data_quality_report.txt"):
    """
    Genera reporte de calidad con métricas de separabilidad.
    """
    report = []

    # Separación inter-clase
    rest_mean = df[df['label']=='REST']['ch3'].mean()
    rest_std = df[df['label']=='REST']['ch3'].std()

    for gesture in ['LEFT', 'RIGHT', 'UP']:
        g_data = df[df['label']==gesture]['ch3']
        separation = abs(g_data.mean() - rest_mean)
        snr = separation / rest_std if rest_std > 0 else 0

        report.append(f"{gesture}:")
        report.append(f"  Separación: {separation:.1f} (meta: >60)")
        report.append(f"  SNR: {snr:.2f} (meta: >3.0)")
        report.append(f"  Intra-class std: {g_data.std():.1f} (meta: <20)")

    # Outliers
    for ch in ['ch1', 'ch2', 'ch3']:
        outlier_pct = (df[ch].abs() > 150).sum() / len(df) * 100
        report.append(f"{ch} outliers: {outlier_pct:.1f}% (meta: <5%)")

    with open(output_path, 'w') as f:
        f.write('\n'.join(report))

    print('\n'.join(report))

# Llamar antes de train_multiclass_model()
evaluate_data_quality(df)
```

**Entregable:** Script actualizado + reporte de calidad de datos actuales

---

### **Prioridad 3: Validación y Visualización**

#### **Tarea 3.1: Crear Dashboard de Calidad**

**Responsable:** Equipo de visualización  
**Plazo:** 1 semana

**Requisitos:**

- Script Python que genere automáticamente:
  1. Boxplots por canal y clase
  2. Histogramas con overlap coefficient
  3. Time series con marcadores de transición
  4. Scatter 3D (ch1 vs ch2 vs ch3) coloreado por clase
  5. Feature importance del modelo

**Entregable:** Script `generate_quality_plots.py` + carpeta `plots/`

---

#### **Tarea 3.2: Establecer Criterios de Aceptación**

**Responsable:** Lead técnico  
**Plazo:** 2 días

**Definir umbrales mínimos para considerar datos "aptos":**

```python
QUALITY_THRESHOLDS = {
    'min_separation_ch3': 60,      # Separación mínima vs REST
    'max_intra_class_std': 20,     # Varianza dentro de clase
    'max_outlier_percentage': 5,   # % de outliers
    'min_snr': 3.0,                # Signal-to-noise ratio
    'max_overlap_coefficient': 0.3 # Overlap entre histogramas
}
```

**Entregable:** Documento `quality_standards.md` con criterios + ejemplos

---

## 📈 4. Métricas de Éxito

### 4.1 Métricas de Datos (Pre-entrenamiento)

| Métrica              | Actual | Meta Corto Plazo | Meta Final |
| -------------------- | ------ | ---------------- | ---------- |
| Separación CH3 LEFT  | ~30    | 60               | 80         |
| Separación CH3 RIGHT | ~10    | 40               | 60         |
| Separación CH3 UP    | ~0     | 30               | 50         |
| Overlap REST-UP      | >80%   | <50%             | <30%       |
| Outliers %           | ~8%    | <5%              | <3%        |

### 4.2 Métricas de Modelo (Post-entrenamiento)

| Métrica         | Actual | Meta Corto Plazo | Meta Final |
| --------------- | ------ | ---------------- | ---------- |
| Accuracy global | 67%    | 75%              | >85%       |
| Precision LEFT  | ~75%   | 85%              | >90%       |
| Precision RIGHT | ~60%   | 70%              | >80%       |
| Precision UP    | ~55%   | 65%              | >75%       |
| Recall REST     | ~70%   | 80%              | >85%       |

---

## 🗓️ 5. Cronograma

### **Semana 1 (28 ene - 3 feb)**

- [ ] Tarea 2.1: Filtro de transiciones
- [ ] Tarea 2.2: Métricas de calidad
- [ ] Tarea 3.2: Criterios de aceptación
- [ ] Evaluación de datos actuales con nuevas métricas

### **Semana 2 (4 feb - 10 feb)**

- [ ] Tarea 1.1: Nuevo protocolo 2s/2s
- [ ] Tarea 1.2: Experimento CH1/CH2
- [ ] Tarea 3.1: Dashboard de calidad
- [ ] Recolectar datos piloto con nuevo protocolo

### **Semana 3 (11 feb - 17 feb)**

- [ ] Análisis comparativo: datos antiguos vs nuevos
- [ ] Ajustar umbrales de filtrado según resultados
- [ ] Re-entrenar modelo con mejor dataset
- [ ] Validación en tiempo real

### **Semana 4 (18 feb - 24 feb)**

- [ ] Testing con usuarios finales
- [ ] Ajustes finales de protocolo
- [ ] Documentación de pipeline completo
- [ ] Reporte final de mejora

---

## 🔬 6. Hipótesis a Validar

### H1: Gestos más intensos mejoran separación

- **Test:** Comparar ch3_mean con instrucciones "normal" vs "exagerado"
- **Criterio éxito:** Incremento >50% en separación

### H2: Calibración local reduce drift

- **Test:** Comparar baseline stability con calibración única vs per-trial
- **Criterio éxito:** Reducción >30% en std de REST

### H3: CH2 puede aportar información

- **Test:** Feature importance de RandomForest con gestos nuevos
- **Criterio éxito:** CH2 features en top-10

### H4: Ventanas más largas reducen ruido

- **Test:** Comparar accuracy con windows de 8 vs 12 vs 16 samples
- **Criterio éxito:** Incremento >5% accuracy con ventana óptima

---

## 📚 7. Referencias Técnicas

### Scripts relevantes:

- [`model.py`](../model.py) - Pipeline de entrenamiento actual
- [`data_labeler.py`](../data_labeler.py) - Recolección de datos
- [`balance_data.py`](../balance_data.py) - Función de balanceo
- [`gyro/gyro_monitor.py`](../gyro/gyro_monitor.py) - Monitor en tiempo real

### Reportes previos:

- [Reporte 5](reporte5.md) - RandomForest + Feature Clipping (actual)
- [Reporte 2](reporte2.md) - Experimentos con filtrado
- [Reporte 1](reporte1.md) - Test balanceo inicial

---

## 💬 8. Notas del Equipo

### Observaciones adicionales:

1. **Posicionamiento del headband:** Validar que ubicación sea consistente entre sesiones
2. **Fatiga del usuario:** Sesiones >10min pueden degradar calidad de gestos
3. **Adaptación individual:** Considerar modelos personalizados si separación general no mejora

### Preguntas abiertas:

- ¿Deberíamos considerar otros sensores (accelerómetro)?
- ¿Vale la pena explorar deep learning con datos temporales raw?
- ¿Cómo manejar variabilidad inter-sujeto en producción?

---

## ✅ 9. Checklist de Implementación

### Para equipo de adquisición:

- [ ] Actualizar `data_labeler.py` con timing 2s/2s
- [ ] Crear script de validación de intensidad de gestos
- [ ] Recolectar 3 datasets piloto con nuevo protocolo
- [ ] Documentar instrucciones de gestos para usuarios

### Para equipo de ML:

- [ ] Implementar filtro de gradientes
- [ ] Agregar función `evaluate_data_quality()`
- [ ] Crear script de comparación antes/después
- [ ] Actualizar documentación de pipeline

### Para equipo de validación:

- [ ] Diseñar experimento CH1/CH2 (3 variantes × 20 trials)
- [ ] Ejecutar pruebas piloto con 3 sujetos
- [ ] Generar gráficas comparativas
- [ ] Recomendar mejor variante de gestos

### Para todos:

- [ ] Review de código en PR
- [ ] Actualizar README con nuevos criterios
- [ ] Meeting de seguimiento semanal (jueves 3pm)
- [ ] Compartir resultados en canal #bci-dev

---

**Próxima reunión:** Jueves 30 de enero, 3:00 PM  
**Agenda:** Revisión de métricas actuales + asignación de tareas

---

_Documento generado el 28 de enero de 2026_  
_Última actualización: v1.0_
