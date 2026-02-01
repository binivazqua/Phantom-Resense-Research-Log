# Comparación de Enfoques para Control Binario UP vs REST con Muse 2

## Resumen Ejecutivo

Se comparan dos estrategias para diferenciar el comando "UP" (avance) frente a "REST" (reposo) usando únicamente los 4 canales de la Muse 2. El objetivo es identificar cuál enfoque ofrece mayor potencial para control binario de actuadores, considerando el severo solapamiento observado entre ambas clases en los datos actuales.

---

## 1. Enfoque Clásico de Gestos (Reporte 6)

- **Descripción:** Uso de gestos faciales (cejas, mandíbula) para generar señales diferenciables.
- **Resultados:**
  - CH3 es el canal más discriminativo, pero la separación entre "UP" y "REST" es casi nula (~0, IQR -10 a +10).
  - El solapamiento entre "UP" y "REST" supera el 80% (ver histogramas y boxplots).
  - CH1 y CH2 no aportan información útil en la configuración actual.
  - El pipeline depende mucho de la intensidad y consistencia de los gestos, y sufre con la variabilidad y el drift del baseline.
- **Limitaciones:**
  - El modelo no puede diferenciar gestos con señales tan similares.
  - La sobreposición severa limita la precisión alcanzable (<70%).

---

## 2. Enfoque Motor Imagery Híbrido (Hybrid MI)

- **Descripción:** Implementa periodos cortos y alternados de MI (motor imagery) y REST, con etiquetas precisas por muestra y audio cues para guiar al usuario.
- **Ventajas:**
  - Permite análisis de ERD/ERS y comparación directa MI vs REST dentro del mismo trial.
  - Reduce la fatiga y la variabilidad inter-trial.
  - El etiquetado temporal preciso y la estructura de los trials facilitan la extracción de features específicos (mu/beta power, ERD, etc.).
  - Alineado con la literatura (5s MI, 10s REST, ciclos cortos).
- **Limitaciones:**
  - Depende de la capacidad del usuario para generar patrones de MI consistentes.
  - La sensibilidad de la Muse 2 es limitada para MI comparado con sistemas clínicos.

---

## 3. ¿Puede el enfoque MI ayudar a diferenciar UP vs REST?

- **Ventaja clave:** El MI híbrido permite comparar REST y UP (MI) en condiciones idénticas de contexto y baseline, minimizando el drift y la variabilidad.
- **Features temporales:** El análisis de potencia en bandas (mu/beta) y ERD/ERS puede revelar diferencias que no son visibles en los histogramas clásicos de amplitud.
- **Clasificación binaria:** Si bien la separación en el dominio de amplitud es baja, la discriminación puede mejorar usando features de frecuencia y dinámica temporal, especialmente con etiquetas precisas.
- **Limitación:** El éxito depende de la capacidad del usuario para generar patrones de MI consistentes y de la sensibilidad de los 4 canales de la Muse 2.

---

## 4. Recomendaciones

- El enfoque de MI híbrido es prometedor para la diferenciación binaria "UP" vs "REST", especialmente si se explotan features de frecuencia y se usan pipelines de análisis adaptados (ERD/ERS, SNR, etc.).
- Validar experimentalmente si realmente se observa una diferencia estadísticamente significativa entre MI y REST en los datos, usando las nuevas métricas propuestas (separación, SNR, overlap).
- Si la diferencia es marginal, explorar técnicas de procesamiento avanzado (filtrado adaptativo, deep learning) o considerar la integración de otros sensores.

---

## 5. Conclusión

El enfoque clásico de gestos tiene un límite claro por el solapamiento, pero el enfoque de MI híbrido, aunque más desafiante y dependiente del usuario, abre la puerta a una diferenciación binaria más robusta entre "UP" y "REST" si se aprovechan las ventajas del diseño experimental y el análisis de features temporales/frecuenciales.

---

**Acción sugerida:**

- Realizar pruebas piloto con el protocolo MI híbrido y analizar métricas de separabilidad y SNR.
- Compartir resultados y ajustar el pipeline según los hallazgos.
