// --- Elements ---
const pasteBtn = document.getElementById('pasteBtn');
const videoUrlInput = document.getElementById('videoUrl');
const downloadForm = document.getElementById('downloadForm');
const statusBox = document.getElementById('statusMessage');
const submitBtn = document.getElementById('submitBtn');

const policyModal = document.getElementById('policyModal');
const closeModalBtn = document.getElementById('closeModal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');

const BACKEND_URL = 'https://omnigrab-api.onrender.com';

// --- PASTE BUTTON LOGIC ---
pasteBtn.addEventListener('click', async () => {
    try {
        const text = await navigator.clipboard.readText();
        videoUrlInput.value = text;
        videoUrlInput.focus();
    } catch (err) {
        alert('Please allow clipboard permissions in your browser, or paste manually.');
    }
});

// --- DOWNLOAD LOGIC (Two-Step Architecture) ---
downloadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const urlInput = videoUrlInput.value;
    
    submitBtn.disabled = true;
    submitBtn.classList.add('is-loading'); 
    
    statusBox.className = 'hidden';
    statusBox.textContent = '';

    try {
        // STEP 1: Ask backend to extract the video
        const prepareEndpoint = 'https://omnigrab-api.onrender.com/api/prepare';
        const response = await fetch(prepareEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: urlInput })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to extract media. Please check the link.');
        }

        // STEP 2: Trigger native download
        statusBox.textContent = 'Extraction complete. Starting download...';
        statusBox.className = 'success';
        
        // Use an invisible link to force the browser to save the file
        const downloadLink = document.createElement('a');
        downloadLink.href = `https://omnigrab-api.onrender.com/api/download/${encodeURIComponent(data.filename)}`;
        downloadLink.setAttribute('download', '');
        downloadLink.style.display = 'none';
        
        // Append it, click it, and remove it instantly
        document.body.appendChild(downloadLink);
        downloadLink.click();
        downloadLink.remove();

        // --- NEW UX FEATURE: Clear the form ---
        // Empty the search bar for the next link
        videoUrlInput.value = '';
        
        // Hide the success message after 4 seconds so the UI looks clean again
        setTimeout(() => {
            statusBox.classList.add('hidden');
            statusBox.textContent = '';
        }, 4000);
        
    } catch (error) {
        statusBox.textContent = error.message;
        statusBox.className = 'error';
    } finally {
        submitBtn.disabled = false;
        submitBtn.classList.remove('is-loading');
    }
});

// --- MODAL & POLICY LOGIC ---
const policyContent = {
    tos: {
        title: "Terms of Service",
        html: `
            <p>Welcome to OmniGrab. By using our service, you agree to these terms.</p>
            <h3>1. Acceptable Use</h3>
            <p>Our service is provided for personal, non-commercial use only. You agree to only download content for which you have the creator's permission, or content that falls under public domain or fair use.</p>
            <h3>2. Liability</h3>
            <p>OmniGrab is provided "as is" without warranties of any kind. We are not responsible for the content downloaded through our tool, nor any copyright infringements committed by end-users.</p>
            <h3>3. Service Availability</h3>
            <p>We reserve the right to modify, suspend, or discontinue the service at any time without notice.</p>
        `
    },
    privacy: {
        title: "Privacy Policy",
        html: `
            <p>Your privacy is important to us. OmniGrab is designed to collect as little data as possible.</p>
            <h3>1. Data We Do Not Collect</h3>
            <p>We do not require user accounts. We do not track your download history, and we do not store the URLs you process on our servers permanently.</p>
            <h3>2. Temporary Processing</h3>
            <p>When you submit a URL, it is processed momentarily by our servers. Once the download is passed to your browser, the temporary file is immediately and permanently deleted.</p>
            <h3>3. Analytics</h3>
            <p>We may use basic, anonymized web analytics to monitor server traffic and performance.</p>
        `
    },
    dmca: {
        title: "DMCA Policy",
        html: `
            <p>OmniGrab is a transient proxy service. <strong>We do not host, store, or index any copyrighted media on our servers.</strong></p>
            <p>When a user enters a URL, our tool simply acts as a bridge between the user and the original platform's Content Delivery Network (CDN).</p>
            <h3>Takedown Requests</h3>
            <p>Because no files are hosted on our servers, we cannot remove content. If you are a copyright owner and wish to have a video removed, you must issue your DMCA takedown notice directly to the host platform (e.g., YouTube, TikTok). Once the host removes the video, it will automatically become unavailable through OmniGrab.</p>
        `
    },
    contact: {
        title: "Contact Us",
        html: `
            <p>Have questions, business inquiries, or need to report an issue with the tool?</p>
            <p>You can reach our development team via email.</p>
            <p><strong>Email:</strong> <a href="mailto:support@omnigrab.com">support@omnigrab.com</a></p>
            <br>
            <p><em>Note: We generally respond within 48-72 hours. Please do not contact us requesting the addition of explicit or adult websites, as they violate our acceptable use policy.</em></p>
        `
    }
};

// Open modal
document.querySelectorAll('.footer-links a').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault(); 
        const policyKey = link.getAttribute('data-policy');
        if (policyContent[policyKey]) {
            modalTitle.textContent = policyContent[policyKey].title;
            modalBody.innerHTML = policyContent[policyKey].html;
            policyModal.classList.remove('hidden');
        }
    });
});

// Close modal via X button
closeModalBtn.addEventListener('click', () => {
    policyModal.classList.add('hidden');
});

// Close modal by clicking outside
policyModal.addEventListener('click', (e) => {
    if (e.target === policyModal) {
        policyModal.classList.add('hidden');
    }
});