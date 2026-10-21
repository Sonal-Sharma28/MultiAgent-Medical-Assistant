// script.js
document.getElementById('diagnosisForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const button = document.getElementById('analyzeButton');
    button.disabled = true;
    button.textContent = 'Analyzing...';
    
    const resultContainer = document.getElementById('result');
    const resultContent = document.getElementById('resultContent');
    
    // Show loading state
    resultContent.innerHTML = '<div class="loading">Analyzing patient data...</div>';
    resultContainer.style.display = 'block';
    
    try {
        const response = await fetch('http://127.0.0.1:8000/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                symptoms: document.getElementById('symptoms').value,
                test_results: document.getElementById('testResults').value,
                medical_history: document.getElementById('medicalHistory').value
            }),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Analysis failed. Please try again.');
        }
        
        const data = await response.json();
        
        // Format the result in a more readable way
        const formattedResult = formatMedicalResult(data.result);
        resultContent.innerHTML = formattedResult;
        resultContainer.style.display = 'block';
    } catch (error) {
        resultContent.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        resultContainer.style.display = 'block';
    } finally {
        button.disabled = false;
        button.textContent = 'Analyze';
    }
});

function formatMedicalResult(result) {
    // Extract the treatment plan summary from the result
    let treatmentPlan = '';
    try {
        // The result might be a string or an object containing the treatment plan
        if (typeof result === 'string') {
            treatmentPlan = result;
        } else if (result.task_output) {
            treatmentPlan = result.task_output;
        } else if (result.treatment_plan) {
            treatmentPlan = result.treatment_plan;
        }
        
        // Clean up the text and format it
        treatmentPlan = treatmentPlan
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
            
        return `
            <div class="treatment-summary">
                <div class="treatment-content">
                    ${treatmentPlan}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error formatting result:', error);
        return `<p class="error">Error formatting the treatment plan. Raw result: ${JSON.stringify(result)}</p>`;
    }
}