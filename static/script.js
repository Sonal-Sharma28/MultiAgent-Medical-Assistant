function appendInlineMarkdown(parent, text) {
    const pattern = /(\*\*.+?\*\*|__.+?__|`[^`]+`|\*[^*\n]+\*)/g;
    let lastIndex = 0;

    for (const match of text.matchAll(pattern)) {
        const token = match[0];
        const start = match.index;
        parent.appendChild(document.createTextNode(text.slice(lastIndex, start)));

        const isCode = token.startsWith('`');
        const isBold = token.startsWith('**') || token.startsWith('__');
        const markerLength = isCode || isBold ? 2 : 1;
        const element = document.createElement(isCode ? 'code' : isBold ? 'strong' : 'em');
        element.textContent = token.slice(markerLength, -markerLength);
        parent.appendChild(element);
        lastIndex = start + token.length;
    }

    parent.appendChild(document.createTextNode(text.slice(lastIndex)));
}

function renderMarkdownResult(markdown, container) {
    container.replaceChildren();

    const lines = markdown.replace(/\r\n?/g, '\n').split('\n');
    let paragraphLines = [];
    let listElement = null;
    let listType = null;

    function flushParagraph() {
        if (paragraphLines.length === 0) return;

        const paragraph = document.createElement('p');
        appendInlineMarkdown(paragraph, paragraphLines.join(' '));
        container.appendChild(paragraph);
        paragraphLines = [];
    }

    function flushList() {
        listElement = null;
        listType = null;
    }

    for (const line of lines) {
        const headingMatch = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
        const unorderedMatch = line.match(/^\s*[-*+]\s+(.+)$/);
        const orderedMatch = line.match(/^\s*(\d+)[.)]\s+(.+)$/);

        if (line.trim() === '') {
            flushParagraph();
            flushList();
            continue;
        }

        if (headingMatch) {
            flushParagraph();
            flushList();

            const heading = document.createElement(`h${headingMatch[1].length}`);
            appendInlineMarkdown(heading, headingMatch[2]);
            container.appendChild(heading);
            continue;
        }

        if (unorderedMatch || orderedMatch) {
            flushParagraph();
            const nextListType = orderedMatch ? 'ol' : 'ul';
            if (listType !== nextListType) {
                flushList();
                listType = nextListType;
                listElement = document.createElement(nextListType);
                if (orderedMatch && Number(orderedMatch[1]) !== 1) {
                    listElement.start = Number(orderedMatch[1]);
                }
                container.appendChild(listElement);
            }

            const item = document.createElement('li');
            appendInlineMarkdown(item, orderedMatch ? orderedMatch[2] : unorderedMatch[1]);
            listElement.appendChild(item);
            continue;
        }

        flushList();
        paragraphLines.push(line.trim());
    }

    flushParagraph();
}

document.getElementById('diagnosisForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const button = document.getElementById('analyzeButton');
    const resultContainer = document.getElementById('result');
    const resultContent = document.getElementById('resultContent');
    button.disabled = true;
    button.textContent = 'Analyzing...';
    resultContent.replaceChildren();
    const loadingMessage = document.createElement('div');
    loadingMessage.className = 'loading';
    loadingMessage.textContent = 'Analyzing patient data...';
    resultContent.appendChild(loadingMessage);
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
                medical_history: document.getElementById('medicalHistory')?.value ?? ''
            }),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Analysis failed. Please try again.');
        }

        const result = typeof data.result === 'string'
            ? data.result
            : data.result?.task_output || data.result?.treatment_plan;
        if (typeof result !== 'string') {
            throw new Error('The response did not include a readable result.');
        }

        renderMarkdownResult(result, resultContent);
    } catch (error) {
        resultContent.replaceChildren();
        const errorMessage = document.createElement('p');
        errorMessage.className = 'error';
        errorMessage.textContent = `Error: ${error instanceof Error ? error.message : 'Analysis failed. Please try again.'}`;
        resultContent.appendChild(errorMessage);
    } finally {
        button.disabled = false;
        button.textContent = 'Analyze';
    }
});