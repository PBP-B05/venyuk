document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('addBlogModal');
  const openBtn = document.getElementById('btn-open-modal');
  const closeBtn = document.getElementById('btn-close-modal');
  const form = document.getElementById('blog-form');

  if (!modal || !form || !openBtn) return;

  // Buka modal
  openBtn.addEventListener('click', () => {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  });

  // Tutup modal
  closeBtn?.addEventListener('click', () => {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  });

  // Handle submit AJAX
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  console.log('Form submit triggered');

  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  const postUrl = openBtn.dataset.url || form.action;

  // Ambil data dari form secara manual, BUKAN pakai FormData()
  const data = {
    title: form.querySelector('[name="title"]').value,
    content: form.querySelector('[name="content"]').value,
    category: form.querySelector('[name="category"]')?.value || "community posts",
    thumbnail: form.querySelector('[name="thumbnail"]').value, // ambil URL
  };

  try {
    const response = await fetch(postUrl, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams(data),
    });

    if (response.ok) {
      console.log("✅ Blog berhasil ditambahkan!");
      form.reset();
      modal.classList.add('hidden');
      modal.classList.remove('flex');
      location.reload();
    } else {
      const errText = await response.text();
      console.error("Response error:", errText);
      alert("Gagal menambahkan blog. Coba lagi!");
    }
  } catch (error) {
    console.error("Fetch error:", error);
    alert("Terjadi kesalahan jaringan.");
  }
});

});
