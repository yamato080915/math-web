function latexevent(input, output) {
    const latexCode = input.value;
	const formatted = latexCode.replace(/\n/g, "<br>");
	output.innerHTML = `${formatted}`;
	MathJax.typesetClear();
	MathJax.typesetPromise([output]);
}

function listener(input, output) {
    let debounceTimer
    const debounceDelay = 1000;
    input.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            latexevent(input, output);
        }, debounceDelay);
    });
}