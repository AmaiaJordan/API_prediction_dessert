document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const resultado = document.getElementById('resultado');
    const edadInput = document.getElementById('edad');
    
    // Validar la edad cuando cambia
    edadInput.addEventListener('input', function() {
        const edad = parseInt(this.value);
        const errorMessage = this.parentElement.querySelector('.error-message');
        
        if (edad < 18 || edad > 90) {
            this.classList.add('error');
            errorMessage.style.display = 'block';
        } else {
            this.classList.remove('error');
            errorMessage.style.display = 'none';
        }
    });
    
    // Manejar el envío del formulario
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Verificar la edad
        const edad = parseInt(edadInput.value);
        if (edad < 18 || edad > 90) {
            alert('Por favor, ingresa una edad válida entre 18 y 90 años');
            edadInput.focus();
            return;
        }
        
        // Verificar que todas las opciones estén seleccionadas
        const selects = form.querySelectorAll('select');
        let allSelected = true;
        
        selects.forEach(select => {
            if (!select.value) {
                allSelected = false;
                const group = select.closest('.form-group');
                group.classList.add('error');
            } else {
                const group = select.closest('.form-group');
                group.classList.remove('error');
            }
        });
        
        if (!allSelected) {
            alert('Por favor, selecciona todas las opciones');
            return;
        }
        
        try {
            // Mostrar indicador de carga
            const submitButton = form.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            submitButton.disabled = true;
            
            // Preparar los datos para enviar
            const formData = {
                edad: edad,
                genero: document.getElementById('genero').value,
                entrante: document.getElementById('entrante').value,
                primer_plato: document.getElementById('primer_plato').value,
                segundo_plato: document.getElementById('segundo_plato').value,
                bebida: document.getElementById('bebida').value
            };
            
            console.log('Enviando datos:', formData);
            
            // Enviar la petición al servidor
            const response = await fetch('/predecir', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            
            const data = await response.json();
            console.log('Respuesta recibida:', data);
            
            if (data.success) {
                // Mostrar el resultado
                const postreNombre = document.getElementById('postre-nombre');
                const probabilidadBarra = document.getElementById('probabilidad-barra');
                const probabilidadValor = document.getElementById('probabilidad-valor');
                
                postreNombre.textContent = data.postre;
                
                const probabilidad = Math.round(data.probabilidad * 100);
                probabilidadBarra.style.width = probabilidad + '%';
                probabilidadBarra.textContent = probabilidad + '%';
                probabilidadValor.textContent = probabilidad;
                
                // Mostrar el contenedor de resultado con una animación
                resultado.style.display = 'block';
                
                // Hacer scroll suave hasta el resultado
                resultado.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                throw new Error(data.message || 'Error al procesar la predicción');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al comunicarse con el servidor. Por favor, intenta nuevamente.');
        } finally {
            // Restaurar el botón
            const submitButton = form.querySelector('button[type="submit"]');
            submitButton.innerHTML = originalButtonText;
            submitButton.disabled = false;
        }
    });
});
