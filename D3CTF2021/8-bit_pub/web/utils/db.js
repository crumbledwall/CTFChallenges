let mysql = require("mysql");

let connection = mysql.createConnection({
  host: "8-bit-pub-db",
  user: "root",
  password: "365b46bf78edcfa0650c99e4f8e0336a",
  database: "8-bit-pub",
});

connection.connect(function (err) {
  if (err) throw err;
});

module.exports = connection;
