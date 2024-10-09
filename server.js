const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const dbPath = path.join(__dirname, 'ingredients.json');

const readDatabase = (callback) => {
  fs.readFile(dbPath, 'utf-8', (err, data) => {
    if (err) throw err;
    callback(JSON.parse(data));
  });
};

const writeDatabase = (data, callback) => {
  fs.writeFile(dbPath, JSON.stringify(data, null, 2), 'utf-8', (err) => {
    if (err) throw err;
    callback();
  });
};

app.post('/inventory/:userId/add', (req, res) => {
  const { ingredient_name, quantity, unit, expiry_date } = req.body;
  const userId = parseInt(req.params.userId);

  if (isNaN(userId)) {
    return res.status(400).json({ error: 'Invalid user ID.' });
  }

  readDatabase((data) => {
    const newIngredient = {
      id: Date.now(),
      user_id: userId,
      ingredient_name,
      quantity,
      unit,
      expiry_date
    };

    data.push(newIngredient);

    writeDatabase(data, () => {
      res.status(201).json({ message: 'Ingredient added', ingredient: newIngredient });
    });
  });
});

app.delete('/inventory/:userId/delete/:ingredientId', (req, res) => {
  const { userId, ingredientId } = req.params;

  readDatabase((data) => {
    const updatedData = data.filter(ingredient => ingredient.id !== parseInt(ingredientId) || ingredient.user_id !== parseInt(userId));

    writeDatabase(updatedData, () => {
      res.json({ message: 'Ingredient deleted' });
    });
  });
});

app.get('/notifications/:userId', (req, res) => {
  const userId = parseInt(req.params.userId);
  const currentDate = new Date();
  const threeDaysFromNow = new Date();
  threeDaysFromNow.setDate(currentDate.getDate() + 3);

  readDatabase((data) => {
    const expiringIngredients = data.filter(ingredient => 
      ingredient.user_id === userId &&
      new Date(ingredient.expiry_date) <= threeDaysFromNow &&
      new Date(ingredient.expiry_date) >= currentDate
    );
    res.json(expiringIngredients);
  });
});

app.listen(3000, () => {
  console.log('Server running on http://localhost:3000');
});
