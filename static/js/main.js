import { Connection, clusterApiUrl, PublicKey } from "@solana/web3.js";
import { Metaplex, walletAdapterIdentity } from "@metaplex-foundation/js";

const addForm = document.getElementById("addForm");
addForm.onsubmit = async (e) => {
  e.preventDefault();
  const submitBtn = document.getElementById("submitBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Minting NFT...";

  const name = document.querySelector("input[name='name']").value;
  const description = document.querySelector("textarea[name='description']").value;
  const walletPublicKey = window.walletPublicKey; // set after Phantom connect

  try {
    // 1️⃣ Create backend record
    const backendResp = await fetch("/add_item", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description })
    });
    const item = await backendResp.json();
    if (!item.success) throw new Error(item.error);

    // 2️⃣ Connect Phantom
    if (!window.solana || !window.solana.isPhantom) throw new Error("Phantom not found!");
    await window.solana.connect();
    const wallet = window.solana;

    const connection = new Connection(clusterApiUrl("devnet"), "confirmed");
    const metaplex = Metaplex.make(connection).use(walletAdapterIdentity(wallet));

    // 3️⃣ Mint NFT
    const { nft } = await metaplex.nfts().create({
      name,
      uri: "https://example.com/metadata.json",
      sellerFeeBasisPoints: 500,
    });

    alert(`NFT minted! Explorer: https://explorer.solana.com/address/${nft.address.toString()}?cluster=devnet`);
    window.location.href = `/item/${item.item_id}`;

  } catch (err) {
    console.error(err);
    alert("Error: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Mint NFT";
  }
};
