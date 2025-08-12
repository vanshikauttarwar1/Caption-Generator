document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generateBtn');
    const outputText = document.getElementById('outputText');
    const loadingIndicator = document.getElementById('loading');
    const promptDebug = document.getElementById('prompt-debug');
    const abVariantSpan = document.getElementById('ab-variant');
    const feedbackSection = document.querySelector('.feedback');

    generateBtn.addEventListener('click', async () => {
        // 1. Get user inputs
        const payload = {
            base_request: document.getElementById('base_request').value,
            tone: document.getElementById('tone').value,
            style: document.getElementById('style').value,
            content_format: document.getElementById('content_format').value,
            keywords: document.getElementById('keywords').value,
            char_limit: document.getElementById('char_limit').value
        };

        // Basic validation
        if (!payload.base_request) {
            alert('Please enter a base request.');
            return;
        }

        // 2. Show loading state
        loadingIndicator.classList.remove('hidden');
        outputText.textContent = '';
        promptDebug.textContent = '';
        abVariantSpan.textContent = 'N/A';
        feedbackSection.classList.add('hidden');
        generateBtn.disabled = true;

        try {
            // 3. Make API call to the backend
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'An unknown error occurred.');
            }

            const data = await response.json();

            // 4. Display the results
            outputText.textContent = data.generated_text;
            promptDebug.textContent = data.full_prompt_sent;
            abVariantSpan.textContent = data.prompt_variation_used;
            feedbackSection.classList.remove('hidden');

        } catch (error) {
            outputText.textContent = `Error: ${error.message}`;
        } finally {
            // 5. Hide loading state
            loadingIndicator.classList.add('hidden');
            generateBtn.disabled = false;
        }
    });

    // --- A/B Testing Feedback Handler ---
    document.querySelectorAll('.feedback-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const rating = e.target.getAttribute('data-rating');
            const variation = abVariantSpan.textContent;

            // In a real application, you would send this feedback data
            // to a logging service or analytics platform.
            console.log(`Feedback received: Variation '${variation}' was rated as '${rating}'.`);
            
            // Provide user feedback
            feedbackSection.innerHTML = '<p>Thank you for your feedback!</p>';
        });
    });
});