export const validateFile = (file) => {
    const allowedExtensions = ["mp4", "avi", "mov"];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    return allowedExtensions.includes(fileExtension);
};
