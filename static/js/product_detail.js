/**
 * product_detail.js
 *
 * Maneja la selección de variantes (color/talla) y conversión de moneda
 *
 * Requiere que se inyecten estos datos desde la template:
 * - window.productConfig = {
 *     colorMap: {color_id: {image_url, price, converted_price, color_name}},
 *     variantMap: {color_id: {size_id: {variant_id, image_url, price, converted_price}}},
 *     selectedCurrency: 'USD|COP|EUR',
 *     exchangeRate: number,
 *     currencySymbol: '$|€',
 *     defaultColorId: string|null,
 *     defaultSizeId: string|null
 *   }
 */

document.addEventListener("DOMContentLoaded", function () {
  const config = window.productConfig;
  const { colorMap, variantMap } = config;

  // Elementos del DOM
  const elements = {
    mainImage: document.getElementById("main-image"),
    priceDisplayUSD: document.getElementById("price-display-usd"),
    priceDisplayConverted: document.getElementById("price-display-converted"),
    variantIdInput: document.getElementById("variant_id"),
    addToCartBtn: document.getElementById("add-to-cart-btn"),
    selectedColorName: document.getElementById("selected-color-name"),
    selectedSizeName: document.getElementById("selected-size-name"),
    sizeErrorMessage: document.getElementById("size-error-message"),
    colorBoxes: document.querySelectorAll("#color-selection .color-box"),
    sizeBoxes: document.querySelectorAll("#size-selection .size-box"),
  };

  // Estado actual
  let state = {
    selectedColorId: config.defaultColorId,
    selectedSizeId: config.defaultSizeId,
  };

  // Inicialización
  function init() {
    // Cargar miniaturas de color
    Object.keys(colorMap).forEach((colorId) => {
      const thumb = document.getElementById(`color-thumb-${colorId}`);
      if (thumb) thumb.src = colorMap[colorId].image_url;
    });

    // Selección inicial
    if (state.selectedColorId) {
      selectColor(state.selectedColorId);
      if (state.selectedSizeId) {
        selectSize(state.selectedSizeId);
      }
    }
  }

  // Manejar selección de color
  function selectColor(colorId) {
    state.selectedColorId = colorId;
    const colorData = colorMap[colorId];

    // Actualizar UI
    elements.colorBoxes.forEach((box) =>
      box.classList.remove("selected-option")
    );
    document
      .querySelector(`.color-box[data-color-id="${colorId}"]`)
      ?.classList.add("selected-option");

    elements.selectedColorName.textContent = colorData.color_name;
    elements.mainImage.src = colorData.image_url;

    // Actualizar precios
    updatePriceDisplay(colorData.price, colorData.converted_price);

    // Resetear talla si había una seleccionada
    if (state.selectedSizeId) {
      state.selectedSizeId = null;
      elements.sizeBoxes.forEach((box) =>
        box.classList.remove("selected-option")
      );
      elements.selectedSizeName.textContent = "{% trans 'Ninguna' %}";
      elements.sizeErrorMessage.style.display = "none";
    }

    // Deshabilitar botón hasta selección de talla
    elements.addToCartBtn.disabled = true;
    elements.variantIdInput.value = "";
  }

  // Manejar selección de talla
  function selectSize(sizeId) {
    state.selectedSizeId = sizeId;
    const sizeBox = document.querySelector(
      `.size-box[data-size-id="${sizeId}"]`
    );
    const sizeValue = sizeBox?.dataset.sizeValue || "N/A";

    // Actualizar UI
    elements.sizeBoxes.forEach((box) =>
      box.classList.remove("selected-option")
    );
    sizeBox?.classList.add("selected-option");
    elements.selectedSizeName.textContent = sizeValue;

    // Verificar variante disponible
    const variant = variantMap[state.selectedColorId]?.[sizeId];

    if (variant) {
      // Actualizar imagen si es diferente
      if (variant.image_url !== elements.mainImage.src) {
        elements.mainImage.src = variant.image_url;
      }

      // Actualizar precios
      updatePriceDisplay(variant.price, variant.converted_price);

      // Habilitar botón
      elements.addToCartBtn.disabled = false;
      elements.variantIdInput.value = variant.variant_id;
      elements.sizeErrorMessage.style.display = "none";
    } else {
      // Variante no disponible
      elements.addToCartBtn.disabled = true;
      elements.variantIdInput.value = "";
      elements.sizeErrorMessage.style.display = "block";
    }
  }

  // Actualizar visualización de precios
  function updatePriceDisplay(usdPrice, convertedPrice) {
    const formattedUSD = formatPrice(usdPrice, "USD");
    elements.priceDisplayUSD.textContent = `${formattedUSD} USD`;

    if (config.selectedCurrency !== "USD") {
      const formattedConverted = formatPrice(
        convertedPrice,
        config.selectedCurrency
      );
      elements.priceDisplayConverted.style.display = "block";
      elements.priceDisplayConverted.textContent = formattedConverted;
    } else {
      elements.priceDisplayConverted.style.display = "none";
    }
  }

  // Formatear precio según moneda
  function formatPrice(amount, currency) {
    const numericAmount = parseFloat(amount) || 0;

    if (currency === "USD") {
      return `$${numericAmount.toFixed(2)}`;
    }

    const options = {
      style: "currency",
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: currency === "COP" ? 0 : 2,
    };

    return numericAmount
      .toLocaleString("es-CO", options)
      .replace(/^[^\d]*/, config.currencySymbol);
  }

  // Event listeners
  elements.colorBoxes.forEach((box) => {
    box.addEventListener("click", () => selectColor(box.dataset.colorId));
  });

  elements.sizeBoxes.forEach((box) => {
    box.addEventListener("click", () => {
      if (state.selectedColorId) {
        selectSize(box.dataset.sizeId);
      }
    });
  });

  // Inicializar
  init();
});
