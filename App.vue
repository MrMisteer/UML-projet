<template>
  <div>
    <h1>Mon Inventaire</h1>
    <form id="add-ingredient-form" @submit.prevent="addIngredient">
      <input v-model="newIngredient.ingredient_name" placeholder="Nom de l'ingrédient" required />
      <input v-model="newIngredient.quantity" type="number" placeholder="Quantité" required />
      <input v-model="newIngredient.unit" placeholder="Unité" required />
      <input v-model="newIngredient.expiry_date" type="date" required />
      <button type="submit">Ajouter Ingrédient</button>
    </form>

    <ul id="ingredient-list">
      <li v-for="ingredient in ingredients" :key="ingredient.id">
        {{ ingredient.ingredient_name }} ({{ ingredient.quantity }} {{ ingredient.unit }}) - Expire le : {{ ingredient.expiry_date }}
        <button @click="deleteIngredient(ingredient.id)">Supprimer</button>
      </li>
    </ul>
  </div>
</template>

<script>

export default {
  data() {
    return {
      ingredients: [],
      newIngredient: {
        ingredient_name: '',
        quantity: '',
        unit: '',
        expiry_date: ''
      },
      userId: 1
    };
  },
  mounted() {
    this.fetchIngredients();
    this.checkExpiringIngredients();
  },
  methods: {
    fetchIngredients() {
      fetch(`/inventory/${this.userId}`)
        .then(response => response.json())
        .then(data => {
          this.ingredients = data;
        })
        .catch(error => console.error('Erreur lors de la récupération des ingrédients:', error));
    },
    addIngredient() {
      fetch(`/inventory/${this.userId}/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.newIngredient)
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Erreur réseau.');
        }
        return response.json();
      })
      .then(() => {
        this.fetchIngredients();
        this.newIngredient = { ingredient_name: '', quantity: '', unit: '', expiry_date: '' };
      })
      .catch(error => console.error('Erreur lors de l\'ajout de l\'ingrédient:', error));
    },
    deleteIngredient(id) {
      fetch(`/inventory/${this.userId}/delete/${id}`, { method: 'DELETE' })
        .then(() => {
          this.fetchIngredients();
        })
        .catch(error => console.error('Erreur lors de la suppression de l\'ingrédient:', error));
    },
    checkExpiringIngredients() {
  fetch(`/notifications/${this.userId}`)
    .then(response => response.json())
    .then(data => {
      if (data.length > 0) {
        this.$toast.warning('Vous avez des ingrédients proches d\'expirer !');
      }
    })
    .catch(error => console.error('Erreur lors de la vérification des ingrédients expirants:', error));
  }

  }
};
</script>

