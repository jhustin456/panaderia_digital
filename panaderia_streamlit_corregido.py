import streamlit as st
import pandas as pd

# ==========================================================
# SISTEMA DE PANADERIA DIGITAL - VERSION CON STREAMLIT
# Interfaz grafica basada en el programa original.
# ==========================================================

st.set_page_config(page_title="Panaderia digital", page_icon="🥖", layout="wide")

# Guardamos los datos mientras la aplicacion este abierta.
listas = {
    "codigo": [],
    "nom": [],
    "p_produ": [],
    "costo_agua": [],
    "p_venta": [],
    "stock": [],
}
for nombre, valor_inicial in listas.items():
    if nombre not in st.session_state:
        st.session_state[nombre] = valor_inicial.copy()

codigo = st.session_state.codigo
nom = st.session_state.nom
p_produ = st.session_state.p_produ
costo_agua = st.session_state.costo_agua
p_venta = st.session_state.p_venta
stock = st.session_state.stock

st.title("🥖 Panadería digital")
st.write("Registro de productos, análisis de precios sugeridos y control de inventario.")

if not st.session_state.get("inicio_confirmado", False):
    st.info("Bienvenido. Registra tus productos para comenzar a utilizar el sistema.")
    if st.button("Continuar", type="primary"):
        st.session_state.inicio_confirmado = True
        st.rerun()

if st.session_state.get("inicio_confirmado", False):
    pesta_registro, pesta_precios, pesta_inventario, pesta_resumen = st.tabs(
        ["Registrar productos", "Precios sugeridos", "Control de inventario", "Ver productos"]
    )

    # ------------------------------------------------------
    # PARTE 1. REGISTRAR PRODUCTOS
    # ------------------------------------------------------
    with pesta_registro:
        st.header("Registro de productos")
        st.write("Primero ingresa los datos del recibo de agua y el método de limpieza.")

        with st.form("form_registro", clear_on_submit=False):
            prod_r = st.number_input(
                "¿Cuántos productos desea registrar?",
                min_value=1, max_value=50, value=1, step=1
            )
            st.subheader("Datos del servicio de agua")
            recibo = st.number_input("Valor total del recibo del agua ($)", min_value=0.01, value=10000.0, step=1000.0)
            mtrs_c = st.number_input("Metros cúbicos (m³) gastados en el mes", min_value=0.01, value=10.0, step=1.0)

            st.subheader("Método de limpieza")
            mtdo_texto = st.radio(
                "Seleccione el método de limpieza que maneja la panadería:",
                ["Individual por producto", "General al final del día/turno"]
            )
            mtdo = 1 if mtdo_texto == "Individual por producto" else 2

            if mtdo == 2:
                min_t = st.number_input(
                    "Total de minutos que estuvo la manguera abierta en la limpieza",
                    min_value=0.01, value=10.0, step=1.0
                )
            else:
                min_t = 0.0

            st.subheader("Datos de cada producto")
            datos_productos = []
            for p in range(int(prod_r)):
                st.markdown(f"**Producto {p + 1} de {int(prod_r)}**")
                col1, col2 = st.columns(2)
                with col1:
                    c = st.text_input(
                        "Código de 4 caracteres",
                        max_chars=4,
                        key=f"codigo_{p}",
                        placeholder="Ej. A001"
                    )
                    n = st.text_input(
                        "Nombre del producto",
                        key=f"nombre_{p}",
                        placeholder="Ej. Pan de queso"
                    )
                    produ = st.number_input(
                        "Costo de producción por lote ($)",
                        min_value=0.01, value=10000.0, step=500.0,
                        key=f"produ_{p}"
                    )
                with col2:
                    l_masa = st.number_input(
                        "Litros de agua utilizados en la masa",
                        min_value=0.01, value=2.0, step=0.5,
                        key=f"masa_{p}"
                    )
                    if mtdo == 1:
                        st.caption("Nota: se utiliza un caudal aproximado de 12 litros por minuto.")
                        min_l = st.number_input(
                            "Minutos que estuvo abierto el grifo lavando este lote",
                            min_value=0.01, value=2.0, step=0.5,
                            key=f"minutos_{p}"
                        )
                        umbral_lim = st.number_input(
                            "Umbral de limpieza en litros (recomendado: 50 a 60)",
                            min_value=0.01, value=55.0, step=1.0,
                            key=f"umbral_{p}"
                        )
                    else:
                        min_l = 0.0
                        umbral_lim = 0.0
                    vent = st.number_input(
                        "Precio de venta por unidad ($)",
                        min_value=0.01, value=2000.0, step=100.0,
                        key=f"venta_{p}"
                    )
                    stock_ini = st.number_input(
                        "Unidades iniciales en inventario",
                        min_value=0, value=10, step=1,
                        key=f"stock_{p}"
                    )
                datos_productos.append({
                    "codigo": c, "nombre": n, "produ": produ,
                    "l_masa": l_masa, "min_l": min_l,
                    "umbral": umbral_lim, "venta": vent,
                    "stock": stock_ini
                })
                st.divider()

            enviar_registro = st.form_submit_button("Registrar productos", type="primary")

        if enviar_registro:
            errores = []
            codigos_nuevos = []
            for i, dato in enumerate(datos_productos):
                if len(dato["codigo"].strip()) != 4:
                    errores.append(f"El código del producto {i + 1} debe tener exactamente 4 caracteres.")
                if not dato["nombre"].strip():
                    errores.append(f"Escribe el nombre del producto {i + 1}.")
                codigos_nuevos.append(dato["codigo"].strip())

            if recibo <= 0 or mtrs_c <= 0:
                errores.append("El recibo y los metros cúbicos deben ser mayores que cero.")
            if len(set(codigos_nuevos)) != len(codigos_nuevos):
                errores.append("No repitas códigos entre los productos que estás registrando.")

            if errores:
                for error in errores:
                    st.error(error)
            else:
                c_litros_agua = recibo / (mtrs_c * 1000)
                cantidad_registrada = len(datos_productos)
                costos_nuevos = []

                for i, dato in enumerate(datos_productos):
                    if mtdo == 1:
                        ll_prod = dato["min_l"] * 12
                        if ll_prod > dato["umbral"]:
                            st.warning(
                                f"Alerta ODS 6/ODS 12: la limpieza del producto "
                                f"{dato['nombre']} supera el umbral definido."
                            )
                        tl_prod = dato["l_masa"] + ll_prod
                        cos_agua = tl_prod * c_litros_agua
                    else:
                        cos_agua = dato["l_masa"] * c_litros_agua

                    codigo.append(dato["codigo"].strip())
                    nom.append(dato["nombre"].strip())
                    p_produ.append(float(dato["produ"]))
                    costo_agua.append(float(cos_agua))
                    p_venta.append(float(dato["venta"]))
                    stock.append(int(dato["stock"]))
                    costos_nuevos.append(float(cos_agua))

                if mtdo == 2:
                    tl_lim_gral = min_t * 12
                    c_agua_gene_pro = (tl_lim_gral * c_litros_agua) / cantidad_registrada
                    # Se reparte el costo general entre los productos registrados en este formulario.
                    for indice in range(len(costo_agua) - cantidad_registrada, len(costo_agua)):
                        costo_agua[indice] += c_agua_gene_pro
                    st.success(
                        f"El costo de limpieza se repartió equitativamente entre "
                        f"{cantidad_registrada} productos."
                    )

                st.success("¡Registro completado con éxito!")

    # ------------------------------------------------------
    # PARTE 2. CALCULAR PRECIOS SUGERIDOS
    # ------------------------------------------------------
    with pesta_precios:
        st.header("Análisis de precios sugeridos")
        if not codigo:
            st.info("Primero debes registrar al menos un producto.")
        else:
            porc_gana = st.number_input(
                "Porcentaje de ganancia deseado (sin incluir el %)",
                min_value=0.01, value=30.0, step=1.0,
                key="porcentaje_ganancia"
            )
            if st.button("Calcular precios sugeridos", type="primary"):
                resultados = []
                for i in range(len(codigo)):
                    if stock[i] > 0:
                        # Se conserva el cálculo del programa original:
                        # costo por lote dividido entre las unidades en inventario.
                        ins_unit = p_produ[i] / stock[i]
                        agua_lote = costo_agua[i] / stock[i]
                        ct_real = ins_unit + agua_lote
                        prec_s = ct_real * (1 + (porc_gana / 100))
                        resultados.append({
                            "Producto": nom[i],
                            "Código": codigo[i],
                            "Costo de insumos por unidad": ins_unit,
                            "Costo de agua por unidad": agua_lote,
                            "Costo total real por unidad": ct_real,
                            "Precio sugerido": prec_s,
                            "Precio registrado": p_venta[i],
                        })
                    else:
                        st.warning(
                            f"El producto {nom[i]} tiene 0 unidades y no se puede "
                            "calcular su precio por unidad."
                        )

                if resultados:
                    st.dataframe(pd.DataFrame(resultados), use_container_width=True, hide_index=True)
                    st.success("Análisis de precios sugeridos realizado con éxito.")

    # ------------------------------------------------------
    # PARTE 3. GESTIONAR INVENTARIO
    # ------------------------------------------------------
    with pesta_inventario:
        st.header("Control de inventario")
        if not codigo:
            st.info("Primero debes registrar al menos un producto.")
        else:
            opciones = [f"{nom[i]} | Código: {codigo[i]} | Stock: {stock[i]}" for i in range(len(codigo))]
            producto_elegido = st.selectbox("Elija el producto que desea controlar", opciones)
            indice = opciones.index(producto_elegido)

            st.metric("Stock actual", stock[indice])
            deseo = st.radio(
                "¿Qué desea hacer?",
                ["Ver stock", "Sumar unidades", "Restar unidades"],
                horizontal=True
            )

            if deseo == "Sumar unidades":
                cantidad = st.number_input(
                    "¿Cuántas unidades desea sumar?",
                    min_value=1, value=1, step=1, key="sumar_stock"
                )
                if st.button("Sumar al inventario", type="primary"):
                    stock[indice] += int(cantidad)
                    st.success(f"El nuevo stock de {nom[indice]} es: {stock[indice]}")
                    st.rerun()

            elif deseo == "Restar unidades":
                if stock[indice] == 0:
                    st.warning("No hay unidades disponibles para restar.")
                else:
                    cantidad = st.number_input(
                        "¿Cuántas unidades desea restar?",
                        min_value=1, max_value=int(stock[indice]),
                        value=1, step=1, key="restar_stock"
                    )
                    if st.button("Restar del inventario", type="primary"):
                        stock[indice] -= int(cantidad)
                        st.success(f"El stock restante de {nom[indice]} es: {stock[indice]}")
                        st.rerun()
            else:
                st.info(f"El stock actual de {nom[indice]} es: {stock[indice]} unidades.")

    # ------------------------------------------------------
    # RESUMEN DE PRODUCTOS
    # ------------------------------------------------------
    with pesta_resumen:
        st.header("Productos registrados")
        if not codigo:
            st.info("Todavía no hay productos registrados.")
        else:
            tabla = []
            for i in range(len(codigo)):
                tabla.append({
                    "Código": codigo[i],
                    "Producto": nom[i],
                    "Costo de producción por lote": p_produ[i],
                    "Costo de agua": costo_agua[i],
                    "Precio de venta": p_venta[i],
                    "Stock": stock[i],
                })
            st.dataframe(pd.DataFrame(tabla), use_container_width=True, hide_index=True)
            st.caption(f"Total de productos registrados: {len(codigo)}")

st.sidebar.title("Información")
st.sidebar.write("Sistema de panadería digital")
st.sidebar.caption(
    "Los datos se mantienen durante la sesión de la aplicación. "
    "Si se reinicia la sesión, se pueden perder."
)
