function mathjaxupdate(element, text) {
    const formatted = text.replace(/\n/g, "<br>").replace("[終]", '<p style="text-align: right; padding-right: 10%;">(終)</p>');
    element.innerHTML = `${formatted}`;
    MathJax.typesetClear();
    MathJax.typesetPromise([element]);
}
function latexevent(input, output) {
    const latexCode = input.value;
    mathjaxupdate(output, latexCode);
}

function listener(input, output) {
    let debounceTimer;
    const debounceDelay = 1000;
    input.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            latexevent(input, output);
        }, debounceDelay);
    });
}