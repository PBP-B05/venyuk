document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('addBlogModal');
    const openBtn = document.getElementById('btn-open-modal');
    const closeBtn = document.getElementById('btn-close-modal');
    const form = document.getElementById('blog-form');

    if (!modal || !form) return;

    // Buka modal
    openBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    });

    // Tutup modal
    closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    });

    // Handle submit AJAX
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        const response = await fetch("{% url 'blog:add_blog' %}", {
            method: "POST",
            headers: { "X-CSRFToken": csrftoken },
            body: formData,
        });

        if (response.ok) {
            form.reset();
            modal.classList.add('hidden');
            // Reload daftar blog
            location.reload();
        } else {
            alert("Failed to add blog!");
        }
    });
});
