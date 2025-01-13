import React from "react";
import { getDropboxAuthorizeUrl } from "../../api";

const Home = () => {
  const handleAuthorize = async () => {
    const redirectUri = "http://localhost:3000/callback";
    const authorizeUrl = await getDropboxAuthorizeUrl(redirectUri);
    window.location.href = authorizeUrl; // Redirect user to Dropbox authorization
  };

  return (
    <div className="home">
      <h1>Welcome to Dropbox Integration</h1>
      <button onClick={handleAuthorize}>Connect to Dropbox</button>
    </div>
  );
};

export default Home;
