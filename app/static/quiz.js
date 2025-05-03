let selectedStyle = '';
let selectedImages = new Set();
let activeTab = 'tops';

const numImagesByStyle = {
  casual: { tops: 6, bottoms: 4 },
  streetwear: { tops: 5, bottoms: 5 },
  sports: { tops: 4, bottoms: 2 },
  formal: { tops: 3, bottoms: 3 }
};


function openModal(styleName) {
  selectedStyle = styleName;
  updateTabHighlight();
  loadImagesForStyle();
  document.getElementById('styleModal').style.display = 'block';
}

function switchTab(tabName) {
  activeTab = tabName;
  loadImagesForStyle(); // reload images when switching tab
  updateTabHighlight();
}

function updateTabHighlight() {
  document.getElementById('topsTab').classList.toggle('active', activeTab === 'tops');
  document.getElementById('bottomsTab').classList.toggle('active', activeTab === 'bottoms');
}

function loadImagesForStyle() {
  const fitImagesContainer = document.getElementById('fitImages');
  fitImagesContainer.innerHTML = '';

  const gallery = document.createElement('div');
  gallery.className = 'image-gallery';

  const images = [];

  const numImages = (numImagesByStyle[selectedStyle] && numImagesByStyle[selectedStyle][activeTab]) || 0;
  for (let i = 1; i <= numImages; i++) {
    let fileName = `${activeTab}${i}.jpg`;
    let imgPath = `/static/${selectedStyle}/${fileName}`;
    images.push(imgPath);
  }

  images.forEach(imgPath => {
    const img = document.createElement('img');
    img.src = imgPath;
    img.alt = selectedStyle;
    img.className = 'selectable-image';

    const relativePath = img.src.replace(window.location.origin, '');
    if (selectedImages.has(relativePath)) {
      img.classList.add('selected');
    }

    img.onclick = () => {
      if (img.classList.contains('selected')) {
        img.classList.remove('selected');
        selectedImages.delete(relativePath);
      } else {
        img.classList.add('selected');
        selectedImages.add(relativePath);
      }
    };

    gallery.appendChild(img);
  });

  fitImagesContainer.appendChild(gallery);
}

function reviewSelections() {
  if (selectedImages.size === 0) {
    alert('Please select at least one image first!');
    return;
  }

  localStorage.setItem('selectedImages', JSON.stringify(Array.from(selectedImages)));
  window.location.href = '/review';
}

function closeModal() {
  document.getElementById('styleModal').style.display = 'none';
}

function saveSelectionsAndClose() {
    const selectedImages = [];
    document.querySelectorAll('.selectable-image.selected').forEach(img => {
      selectedImages.push(img.src);  // or just the image name
    });
  
    console.log('Selected images:', selectedImages);
  
    // Send to backend
    fetch('/save_selections', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ images: selectedImages })
    }).then(response => {
      if (response.ok) {
        console.log('Selections saved!');
        document.getElementById('styleModal').style.display = 'none';
      } else {
        alert('Failed to save selections.');
      }
    });
  }
  