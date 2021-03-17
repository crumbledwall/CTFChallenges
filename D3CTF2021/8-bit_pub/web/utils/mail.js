const nodemailer = require("nodemailer");

async function send(contents) {
  let transporter = nodemailer.createTransport({
  host: "smtp.server.8-bit.pub", // Plz use your own smtp server for testing
  port: 2525,
  tls: { rejectUnauthorized: false },
  auth: false
});
  return transporter.sendMail(contents);
}

module.exports = send;
