function changeGallery(imagesJson) {
    const images = JSON.parse(imagesJson);
    const container = document.getElementById('image-container');
    container.innerHTML = '';
    images.forEach(src => {
      const img = document.createElement('img');
      img.src = src;
      img.classList.add('gallery-image');
      container.appendChild(img);
    });
  }