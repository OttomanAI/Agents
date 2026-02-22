import pinecone as pinecone_module


def test_upload_chunked_data_to_pinecone_replaces_and_upserts(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_embed_chunks(*, chunks, model, openai_api_key):
        calls["chunks"] = chunks
        calls["model"] = model
        calls["openai_api_key"] = openai_api_key
        return [[0.1, 0.2], [0.3, 0.4]]

    def fake_delete_all_vectors(*, index_host, namespace, pinecone_api_key):
        calls["deleted"] = (index_host, namespace, pinecone_api_key)

    def fake_upsert_vectors(*, index_host, namespace, vectors, pinecone_api_key, batch_size):
        calls["upsert"] = {
            "index_host": index_host,
            "namespace": namespace,
            "vectors": vectors,
            "pinecone_api_key": pinecone_api_key,
            "batch_size": batch_size,
        }
        return len(vectors)

    monkeypatch.setattr(pinecone_module, "_embed_chunks", fake_embed_chunks)
    monkeypatch.setattr(pinecone_module, "_delete_all_vectors", fake_delete_all_vectors)
    monkeypatch.setattr(pinecone_module, "_upsert_vectors", fake_upsert_vectors)

    result = pinecone_module.upload_chunked_data_to_pinecone(
        chunked_data="Chunk A ----KB CHUNK---- Chunk B",
        index_host="example-index-host",
        namespace="sales",
        embedding_size="small",
        replace_existing=True,
        pinecone_api_key="pc-key",
        openai_api_key="oa-key",
    )

    assert calls["model"] == "text-embedding-3-small"
    assert calls["chunks"] == ["Chunk A", "Chunk B"]
    assert calls["deleted"] == ("https://example-index-host", "sales", "pc-key")
    upsert_call = calls["upsert"]
    assert upsert_call["batch_size"] == 100
    assert upsert_call["namespace"] == "sales"
    assert len(upsert_call["vectors"]) == 2
    assert upsert_call["vectors"][0]["metadata"]["text"] == "Chunk A"
    assert result.deleted_existing is True
    assert result.chunk_count == 2
    assert result.upserted_count == 2


def test_upload_chunked_data_to_pinecone_uses_large_model(monkeypatch) -> None:
    monkeypatch.setattr(
        pinecone_module,
        "_embed_chunks",
        lambda **kwargs: [[0.5], [0.6]],
    )
    monkeypatch.setattr(pinecone_module, "_upsert_vectors", lambda **kwargs: 2)
    monkeypatch.setattr(pinecone_module, "_delete_all_vectors", lambda **kwargs: None)

    result = pinecone_module.upload_chunked_data_to_pinecone(
        chunked_data="One----KB CHUNK----Two",
        index_host="https://host",
        embedding_size="large",
        replace_existing=False,
        pinecone_api_key="pc-key",
        openai_api_key="oa-key",
    )

    assert result.embedding_model == "text-embedding-3-large"
    assert result.deleted_existing is False
    assert result.chunk_count == 2


def test_upload_chunked_data_to_pinecone_rejects_invalid_embedding_size() -> None:
    try:
        pinecone_module.upload_chunked_data_to_pinecone(
            chunked_data="Only one chunk",
            index_host="https://host",
            embedding_size="medium",
            pinecone_api_key="pc-key",
            openai_api_key="oa-key",
        )
        assert False, "Expected ValueError for invalid embedding_size"
    except ValueError as exc:
        assert "embedding_size" in str(exc)


def test_upload_chunked_data_to_pinecone_rejects_empty_chunks() -> None:
    try:
        pinecone_module.upload_chunked_data_to_pinecone(
            chunked_data="   ",
            index_host="https://host",
            embedding_size="small",
            pinecone_api_key="pc-key",
            openai_api_key="oa-key",
        )
        assert False, "Expected ValueError for empty chunked_data"
    except ValueError as exc:
        assert "chunked_data" in str(exc)
