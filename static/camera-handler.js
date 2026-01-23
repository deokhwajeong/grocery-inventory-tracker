/**
 * Cross-platform Camera Handler
 * Handles camera functionality for Web (Desktop/Mobile) and Native Apps (iOS/Android)
 * Uses Capacitor Camera API when available, falls back to HTML5 input
 */

class CameraHandler {
    constructor() {
        this.isCapacitorAvailable = false;
        this.isNativeApp = false;
        this.init();
    }

    async init() {
        // Check if running as native app with Capacitor
        if (typeof Capacitor !== 'undefined') {
            this.isCapacitorAvailable = true;
            this.isNativeApp = Capacitor.isNativePlatform();
            console.log('Capacitor detected. Native platform:', this.isNativeApp);
        } else {
            console.log('Running as web app (no Capacitor)');
        }
    }

    /**
     * Get photo from camera or file system
     * @param {string} source - 'camera' or 'photos' or 'prompt'
     * @returns {Promise<{dataUrl: string, file: File}>}
     */
    async getPhoto(source = 'prompt') {
        if (this.isCapacitorAvailable && this.isNativeApp) {
            return await this.getPhotoNative(source);
        } else {
            return await this.getPhotoWeb(source);
        }
    }

    /**
     * Get photo using Capacitor Camera API (Native iOS/Android)
     */
    async getPhotoNative(source) {
        try {
            const { Camera } = Capacitor.Plugins;
            
            const sourceType = source === 'camera' 
                ? Camera.CameraSource.Camera 
                : source === 'photos'
                ? Camera.CameraSource.Photos
                : Camera.CameraSource.Prompt;

            const image = await Camera.getPhoto({
                quality: 90,
                allowEditing: false,
                resultType: Camera.CameraResultType.DataUrl,
                source: sourceType,
                correctOrientation: true,
                saveToGallery: false
            });

            // Convert data URL to File object
            const blob = await this.dataUrlToBlob(image.dataUrl);
            const file = new File([blob], 'receipt.jpg', { type: 'image/jpeg' });

            return {
                dataUrl: image.dataUrl,
                file: file
            };
        } catch (error) {
            console.error('Native camera error:', error);
            throw new Error('Failed to capture photo: ' + error.message);
        }
    }

    /**
     * Get photo using HTML5 file input (Web/PWA)
     */
    async getPhotoWeb(source) {
        return new Promise((resolve, reject) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            
            // Set capture attribute for mobile browsers
            if (source === 'camera' && this.isMobileDevice()) {
                input.capture = 'environment'; // Use back camera
            }

            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) {
                    reject(new Error('No file selected'));
                    return;
                }

                try {
                    const dataUrl = await this.fileToDataUrl(file);
                    resolve({ dataUrl, file });
                } catch (error) {
                    reject(error);
                }
            };

            input.click();
        });
    }

    /**
     * Check if running on mobile device
     */
    isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
            || (navigator.maxTouchPoints && navigator.maxTouchPoints > 2);
    }

    /**
     * Check if running on iOS
     */
    isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    }

    /**
     * Check if running on Android
     */
    isAndroid() {
        return /Android/.test(navigator.userAgent);
    }

    /**
     * Convert data URL to Blob
     */
    async dataUrlToBlob(dataUrl) {
        const response = await fetch(dataUrl);
        return await response.blob();
    }

    /**
     * Convert File to data URL
     */
    fileToDataUrl(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    /**
     * Request camera permissions (for native apps)
     */
    async requestPermissions() {
        if (!this.isCapacitorAvailable || !this.isNativeApp) {
            return true; // Web doesn't need explicit permission request
        }

        try {
            const { Camera } = Capacitor.Plugins;
            const permissions = await Camera.checkPermissions();
            
            if (permissions.camera !== 'granted' || permissions.photos !== 'granted') {
                const result = await Camera.requestPermissions();
                return result.camera === 'granted' && result.photos === 'granted';
            }
            
            return true;
        } catch (error) {
            console.error('Permission request error:', error);
            return false;
        }
    }

    /**
     * Get platform information
     */
    getPlatformInfo() {
        return {
            isNative: this.isNativeApp,
            isCapacitor: this.isCapacitorAvailable,
            isMobile: this.isMobileDevice(),
            isIOS: this.isIOS(),
            isAndroid: this.isAndroid(),
            platform: this.isNativeApp 
                ? (this.isIOS() ? 'iOS' : this.isAndroid() ? 'Android' : 'Unknown Native')
                : (this.isMobileDevice() ? 'Mobile Web' : 'Desktop Web')
        };
    }
}

// Export for use in other scripts
window.CameraHandler = CameraHandler;
