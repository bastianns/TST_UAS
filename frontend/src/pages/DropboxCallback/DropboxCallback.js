import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const DropboxCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get("code");

      if (code) {
        try {
          const response = await fetch(
            `https://sensiwithme.my.id/api/dropbox/callback?code=${code}`
          );
          const data = await response.json();

          if (data.access_token) {
            console.log("Authorization successful:", data.access_token);
            navigate("/dashboard"); // Redirect user to the dashboard
          } else {
            console.error("Error during Dropbox callback:", data.error);
          }
        } catch (error) {
          console.error("Failed to handle Dropbox callback:", error);
        }
      }
    };

    handleCallback();
  }, [navigate]);

  return <div>Processing Dropbox authorization...</div>;
};

export default DropboxCallback;
