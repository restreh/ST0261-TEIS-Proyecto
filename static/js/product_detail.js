/**
 * product_detail.js
 *
 * Este archivo contiene la lógica para la vista de detalle de un producto,
 * que permite actualizar la imagen principal, el precio y el variant_id en función de
 * la selección de color y talla.
 *
 * Se espera que se inyecten dos variables globales:
 *   - window.COLOR_MAP_JSON: Objeto JSON con datos de colores (imagen, precio, color_name)
 *   - window.VARIANT_MAP_JSON: Objeto JSON con datos de variantes (por combinación de color y talla)
 *
 * Requisitos de seguridad:
 *   - El script se aloja de forma externa en la carpeta static.
 *   - Se ejecuta al cargar el DOM (DOMContentLoaded).
 */

document.addEventListener("DOMContentLoaded", function () {
  // Datos inyectados desde la plantilla
  const colorMap = JSON.parse(window.COLOR_MAP_JSON);
  const variantMap = JSON.parse(window.VARIANT_MAP_JSON);

  // Referencias a elementos del DOM
  const mainImage = document.getElementById("main-image");
  const priceDisplay = document.getElementById("price-display");
  const variantIdInput = document.getElementById("variant_id");
  const addToCartBtn = document.getElementById("add-to-cart-btn");
  const selectedColorName = document.getElementById("selected-color-name");
  const selectedSizeName = document.getElementById("selected-size-name");
  const errorMessage = document.getElementById("size-error-message");

  let selectedColorId = null;
  let selectedSizeId = null;

  // Función para formatear el precio usando la configuración regional 'es-CO'
  function formatPrice(num) {
    let n = parseFloat(num);
    if (isNaN(n)) n = 0;
    return n.toLocaleString("es-CO", {
      style: "currency",
      currency: "COP",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
  }

  // Llenar las miniaturas de color
  for (const [colorId, data] of Object.entries(colorMap)) {
    const thumb = document.getElementById(`color-thumb-${colorId}`);
    if (thumb) {
      thumb.src = data.image_url;
    }
  }

  // Seleccionar por defecto el primer color (si existe)
  const colorKeys = Object.keys(colorMap);
  if (colorKeys.length > 0) {
    selectedColorId = colorKeys[0];
    selectedColorName.textContent =
      colorMap[selectedColorId].color_name || "Color " + selectedColorId;
    mainImage.src = colorMap[selectedColorId].image_url;
    priceDisplay.textContent = formatPrice(colorMap[selectedColorId].price);
    // Deshabilitar el botón hasta que se seleccione una talla (si aplica)
    addToCartBtn.disabled = true;
  } else {
    priceDisplay.textContent = formatPrice("{{ product.base_price }}");
  }

  // Función para actualizar la UI (imagen, precio y variant_id)
  function updateUI() {
    if (selectedColorId) {
      if (
        selectedSizeId &&
        variantMap[selectedColorId] &&
        variantMap[selectedColorId][selectedSizeId]
      ) {
        // Si existe la combinación color+talla, usamos los datos específicos
        const data = variantMap[selectedColorId][selectedSizeId];
        mainImage.src = data.image_url;
        priceDisplay.textContent = formatPrice(data.price);
        variantIdInput.value = data.variant_id;
        addToCartBtn.disabled = false;
        errorMessage.style.display = "none";
      } else {
        // Si no se ha seleccionado talla o la combinación no existe, mostramos los datos del color
        mainImage.src = colorMap[selectedColorId].image_url;
        priceDisplay.textContent = formatPrice(colorMap[selectedColorId].price);
        variantIdInput.value = "";
        addToCartBtn.disabled = true;
        // Si se ha seleccionado una talla inválida, se muestra el mensaje de error
        if (
          selectedSizeId &&
          (!variantMap[selectedColorId] ||
            !variantMap[selectedColorId][selectedSizeId])
        ) {
          errorMessage.style.display = "block";
        } else {
          errorMessage.style.display = "none";
        }
      }
    }
  }

  // Manejo de clic en los recuadros de color
  document.querySelectorAll("#color-selection .color-box").forEach((box) => {
    box.addEventListener("click", () => {
      selectedColorId = box.getAttribute("data-color-id");
      selectedColorName.textContent = box.getAttribute("data-color-name");
      // Al cambiar de color, se resetea la selección de talla
      selectedSizeId = null;
      selectedSizeName.textContent = "Ninguna";
      updateUI();
    });
  });

  // Manejo de clic en los recuadros de talla
  document.querySelectorAll("#size-selection .size-box").forEach((box) => {
    box.addEventListener("click", () => {
      selectedSizeId = box.getAttribute("data-size-id");
      selectedSizeName.textContent = box.getAttribute("data-size-value");
      updateUI();
    });
  });
});
